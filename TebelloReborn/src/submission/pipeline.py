# HARD RULE: run_submission() may only ever act on a vacancy that has passed
# the human approval gate (CLAUDE.md Hard Rule #1). The gate admits 'approved'
# and 'submission_failed' — and 'submission_failed' is reachable ONLY from
# 'approved' (see VALID_TRANSITIONS), so admitting it for retries cannot let an
# unapproved application through. Gating is on vacancy.status, never on the mere
# presence of an approvals row, exactly as src/review/cli.py's closing comment
# requires. Adapters never write to the database and never transition status —
# this module owns all persistence, so no adapter can route around the gate.

import logging
from pathlib import Path
from typing import Optional

from src.vacancy_search.db import (
    get_by_id,
    init_db as init_vacancy_db,
    update_vacancy_status,
)
from src.vacancy_search.schema import Vacancy

from .db import init_db as init_submission_db, save_attempt
from .eligibility import get_adapter
from .schema import SubmissionAttempt, SubmissionMethod, SubmissionOutcome
from .session import resolve_session_state_path, session_state_available

logger = logging.getLogger(__name__)

# Statuses a submission may act on. Nothing before the approval gate appears
# here, and that is the whole of Hard Rule #1's enforcement at this layer.
ELIGIBLE_STATUSES = {"approved", "submission_failed"}

MANUAL_DETAIL = "operator-asserted manual submission"

# NOT_SUPPORTED maps to no transition on purpose: the application still needs
# Tebello's action, so the status must keep saying so.
_OUTCOME_STATUS: dict[SubmissionOutcome, Optional[str]] = {
    SubmissionOutcome.SUBMITTED: "submitted",
    SubmissionOutcome.FAILED: "submission_failed",
    SubmissionOutcome.NOT_SUPPORTED: None,
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
    vacancy: Vacancy, manual: bool
) -> tuple[SubmissionMethod, SubmissionOutcome, str]:
    """Work out what happened, without touching the database."""
    if manual:
        # The system cannot witness a manual submission — it records the
        # operator's assertion that one happened, and says so.
        return SubmissionMethod.MANUAL, SubmissionOutcome.SUBMITTED, MANUAL_DETAIL

    adapter = get_adapter(vacancy)
    if adapter is None:
        return (
            SubmissionMethod.AUTO,
            SubmissionOutcome.NOT_SUPPORTED,
            f"no auto-submit adapter for platform '{vacancy.platform}'",
        )

    if not session_state_available():
        return (
            SubmissionMethod.AUTO,
            SubmissionOutcome.FAILED,
            f"no saved browser session at {resolve_session_state_path()} — "
            "run the one-time login setup first",
        )

    try:
        succeeded, detail = adapter.submit(vacancy, resolve_session_state_path())
    except Exception as exc:  # adapter bugs are data, not a reason to kill a batch
        logger.warning("Submission adapter raised for vacancy %s: %s", vacancy.id, exc)
        return SubmissionMethod.AUTO, SubmissionOutcome.FAILED, f"adapter raised: {exc}"

    outcome = SubmissionOutcome.SUBMITTED if succeeded else SubmissionOutcome.FAILED
    return SubmissionMethod.AUTO, outcome, detail


def run_submission(
    vacancy: Vacancy,
    *,
    manual: bool = False,
    db_path: Optional[Path] = None,
) -> SubmissionAttempt:
    """Submit one approved application, or record why it wasn't submitted.

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

        method, outcome, detail = _decide(current, manual)

        attempt = SubmissionAttempt(
            vacancy_id=current.id, method=method, outcome=outcome, detail=detail
        )

        submission_conn = init_submission_db(db_path)
        try:
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
