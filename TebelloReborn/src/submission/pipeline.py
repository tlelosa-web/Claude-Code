# HARD RULE: run_submission() may only ever act on a vacancy that has passed
# the human approval gate (CLAUDE.md Hard Rule #1). The gate admits 'approved'
# and 'submission_failed' — and 'submission_failed' is reachable ONLY from
# 'approved' (see VALID_TRANSITIONS), so admitting it for retries cannot let an
# unapproved application through. Gating is on vacancy.status, never on the mere
# presence of an approvals row, exactly as src/review/cli.py's closing comment
# requires. Adapters never write to the database and never transition status —
# this module owns all persistence, so no adapter can route around the gate.
#
# The same rule extends past the CV and cover letter to every generated word an
# employer reads: _decide() consults submission_prep_ready() before any adapter
# runs, so a vacancy whose screening answers are still pending or rejected
# cannot be submitted (Amendment A2).

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from src.vacancy_search.db import (
    get_by_id,
    init_db as init_vacancy_db,
    update_vacancy_status,
)
from src.vacancy_search.schema import Vacancy

from .db import init_db as init_submission_db, save_attempt, submission_prep_ready
from .eligibility import get_adapter
from .schema import SubmissionAttempt, SubmissionMethod, SubmissionOutcome
from .session import resolve_session_profile_dir, session_state_available

logger = logging.getLogger(__name__)

# Statuses a submission may act on. Nothing before the approval gate appears
# here, and that is the whole of Hard Rule #1's enforcement at this layer.
ELIGIBLE_STATUSES = {"approved", "submission_failed"}

MANUAL_DETAIL = "operator-asserted manual submission"

BATCH_REFUSAL_DETAIL = "auto-submit requires an explicit --vacancy-id"

# NOT_SUPPORTED and PENDING_REVIEW both map to no transition, for the same
# reason: the application still needs Tebello's action, so the status must keep
# saying so. They differ only in which action — submit by hand, versus run
# prep-submission/review-questions (Amendment A3).
_OUTCOME_STATUS: dict[SubmissionOutcome, Optional[str]] = {
    SubmissionOutcome.SUBMITTED: "submitted",
    SubmissionOutcome.FAILED: "submission_failed",
    SubmissionOutcome.NOT_SUPPORTED: None,
    SubmissionOutcome.PENDING_REVIEW: None,
}


class SubmissionNotAllowedError(Exception):
    """Raised when a vacancy has not passed the human approval gate.

    Deliberately an exception rather than a returned value: Hard Rule #1 is the
    one condition that must be impossible to ignore by discarding a return.
    """


class SubmissionStatusError(Exception):
    """The attempt was recorded but the status transition failed afterwards.

    Carries the persisted attempt so the caller can tell the operator exactly
    what is on file rather than printing a bare traceback.
    """

    def __init__(self, attempt: SubmissionAttempt, message: str):
        super().__init__(message)
        self.attempt = attempt


def _decide(
    vacancy: Vacancy,
    manual: bool,
    submission_conn: sqlite3.Connection,
    batch: bool,
) -> tuple[SubmissionMethod, SubmissionOutcome, str]:
    """Work out what happened. Reads prep state; writes nothing."""
    if manual:
        # The system cannot witness a manual submission — it records the
        # operator's assertion that one happened, and says so. Nothing this
        # system generated is being sent, so neither the prep gate nor the batch
        # refusal has anything to say about it.
        return SubmissionMethod.MANUAL, SubmissionOutcome.SUBMITTED, MANUAL_DETAIL

    adapter = get_adapter(vacancy)
    if adapter is None:
        return (
            SubmissionMethod.AUTO,
            SubmissionOutcome.NOT_SUPPORTED,
            f"no auto-submit adapter for platform '{vacancy.platform}'",
        )

    # Ahead of the session check on purpose. Every answer below is state that
    # prep already recorded, so none of it needs a live session to read — and a
    # recorded external-ATS finding must not be masked behind "run the login
    # setup", which would send Tebello to fix something that isn't broken.
    readiness = submission_prep_ready(submission_conn, vacancy.id)
    if not readiness.ready:
        return SubmissionMethod.AUTO, readiness.outcome, readiness.reason

    # Last, so a vacancy that also has a real gate reason hears that instead:
    # "run prep-submission" is more use than "use an explicit --vacancy-id" to
    # someone who would have to run prep first anyway (Amendment A15).
    if batch:
        return (
            SubmissionMethod.AUTO,
            SubmissionOutcome.PENDING_REVIEW,
            BATCH_REFUSAL_DETAIL,
        )

    if not session_state_available():
        return (
            SubmissionMethod.AUTO,
            SubmissionOutcome.FAILED,
            f"no saved browser session at {resolve_session_profile_dir()} — "
            "run the one-time login setup first",
        )

    try:
        succeeded, detail = adapter.submit(vacancy, resolve_session_profile_dir())
    except Exception as exc:  # adapter bugs are data, not a reason to kill a batch
        logger.warning("Submission adapter raised for vacancy %s: %s", vacancy.id, exc)
        return SubmissionMethod.AUTO, SubmissionOutcome.FAILED, f"adapter raised: {exc}"

    outcome = SubmissionOutcome.SUBMITTED if succeeded else SubmissionOutcome.FAILED
    return SubmissionMethod.AUTO, outcome, detail


def run_submission(
    vacancy: Vacancy,
    *,
    manual: bool = False,
    batch: bool = False,
    db_path: Optional[Path] = None,
) -> SubmissionAttempt:
    """Submit one approved application, or record why it wasn't submitted.

    `batch` marks a `submit --all` run, which refuses to drive a real submission
    (Amendment A15) — real applications go out one at a time, by explicit id.

    Returns the persisted SubmissionAttempt for every real outcome. Raises only
    when the approval gate refuses (SubmissionNotAllowedError), when the vacancy
    doesn't exist, or when the status transition fails after the attempt was
    already recorded (SubmissionStatusError).
    """
    vacancy_conn = init_vacancy_db(db_path)
    try:
        current = get_by_id(vacancy_conn, vacancy.id)
        if current is None:
            raise ValueError(f"Vacancy {vacancy.id} not found")

        if current.status not in ELIGIBLE_STATUSES:
            raise SubmissionNotAllowedError(
                f"Vacancy {current.id} has status '{current.status}' — only "
                f"{sorted(ELIGIBLE_STATUSES)} may be submitted. An application "
                "must pass the human approval gate first."
            )

        # One connection for both the prep gate's read and the attempt's write:
        # the gate decides what to record, so reading it on a second connection
        # would only widen the window for the two to disagree.
        submission_conn = init_submission_db(db_path)
        try:
            method, outcome, detail = _decide(current, manual, submission_conn, batch)

            attempt = SubmissionAttempt(
                vacancy_id=current.id, method=method, outcome=outcome, detail=detail
            )

            # Committed BEFORE the status transition below. A crash in between
            # leaves a recorded attempt with a stale status (fails closed), never
            # a 'submitted' vacancy with no attempt on file (fails open). Same
            # ordering, and same deliberate trade-off, as run_review_gate.
            attempt.id = save_attempt(submission_conn, attempt)
        finally:
            submission_conn.close()

        new_status = _OUTCOME_STATUS[outcome]
        if new_status is not None:
            try:
                update_vacancy_status(vacancy_conn, current.id, new_status)
            except ValueError as exc:
                raise SubmissionStatusError(
                    attempt,
                    f"Attempt recorded for vacancy {current.id}, but the status "
                    f"could not advance to '{new_status}': {exc}",
                ) from exc

        return attempt
    finally:
        vacancy_conn.close()
