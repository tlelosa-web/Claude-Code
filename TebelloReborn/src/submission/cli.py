"""Stage 6 CLI surface — `career-engine submit`.

Lives here rather than in main.py for the same reason run_review_gate lives in
src/review/cli.py: the stage owns its own operator-facing behaviour, and main.py
stays a thin argparse + dispatch layer.

All persistence and gating happen in pipeline.py. Nothing here decides whether a
submission is allowed — it only reports what happened and sets the exit code.
"""

import sys
from pathlib import Path
from typing import Optional

from src.vacancy_search.db import get_by_id, get_by_status, init_db as init_vacancy_db
from src.vacancy_search.schema import Vacancy

from .pipeline import SubmissionNotAllowedError, SubmissionStatusError, run_submission
from .schema import SubmissionAttempt, SubmissionOutcome


def report_attempt(vacancy: Vacancy, attempt: SubmissionAttempt) -> None:
    """One line per vacancy, with the exact strings an operator needs.

    The not_supported and pending_review wordings are asserted by tests on
    purpose: they are the only outcomes this build can produce, so if either
    stops telling Tebello what to do the feature is useless even while every
    test of the machinery still passes. The two leave the vacancy in the same
    state ('approved'), so this wording is the only thing distinguishing them —
    run a command, versus submit it by hand.
    """
    if attempt.outcome == SubmissionOutcome.NOT_SUPPORTED:
        print(
            f"  Vacancy {vacancy.id} ({vacancy.company} — {vacancy.title}): "
            f"no automated submission available — submit this one by hand.\n"
            f"    {vacancy.url}"
        )
    elif attempt.outcome == SubmissionOutcome.PENDING_REVIEW:
        print(
            f"  Vacancy {vacancy.id} ({vacancy.company} — {vacancy.title}): "
            f"not ready to submit — {attempt.detail}"
        )
    elif attempt.outcome == SubmissionOutcome.SUBMITTED:
        print(f"  Vacancy {vacancy.id}: submitted ({attempt.detail}).")
    else:
        print(f"  Vacancy {vacancy.id}: submission FAILED — {attempt.detail}")


def submit_one(
    vacancy: Vacancy, manual: bool, db_path: Path, batch: bool = False
) -> Optional[SubmissionAttempt]:
    """Returns the attempt, or None if this vacancy could not be submitted at
    all. Callers decide what a None means for their exit code."""
    try:
        attempt = run_submission(vacancy, manual=manual, batch=batch, db_path=db_path)
    except SubmissionNotAllowedError as exc:
        print(f"  Refused: {exc}")
        return None
    except SubmissionStatusError as exc:
        # The attempt IS on file but the status didn't move — say so precisely,
        # rather than letting a traceback imply nothing was recorded.
        print(f"  {exc}")
        return None

    report_attempt(vacancy, attempt)
    return attempt


def _submit_all(manual: bool, db_path: Path) -> None:
    """Every approved vacancy, one at a time. A failure on one does not abandon
    the rest. Only picks up 'approved' — retries of a failed submission are
    explicit, per-vacancy, so a batch run can't silently re-drive them.

    Passes batch=True: a vacancy that would reach a real adapter.submit() is
    refused and recorded as pending_review instead (Amendment A15). Real
    applications go out one at a time, by explicit id.
    """
    conn = init_vacancy_db(db_path)
    try:
        vacancies = get_by_status(conn, "approved")
    finally:
        conn.close()

    if not vacancies:
        print("No approved vacancies to submit.")
        return

    print(f"Submitting {len(vacancies)} approved vacancies.\n")

    counts = {"submitted": 0, "failed": 0, "not supported": 0, "pending review": 0}
    for vacancy in vacancies:
        attempt = submit_one(vacancy, manual, db_path, batch=True)
        if attempt is None or attempt.outcome == SubmissionOutcome.FAILED:
            counts["failed"] += 1
        elif attempt.outcome == SubmissionOutcome.SUBMITTED:
            counts["submitted"] += 1
        elif attempt.outcome == SubmissionOutcome.PENDING_REVIEW:
            # Its own bucket, not folded into 'not supported': one tells Tebello
            # to submit by hand, the other that a single prep-submission run may
            # unblock the lot.
            counts["pending review"] += 1
        else:
            counts["not supported"] += 1

    print(
        f"\nDone — submitted: {counts['submitted']}, failed: {counts['failed']}, "
        f"not supported: {counts['not supported']}, "
        f"pending review: {counts['pending review']}"
    )

    # 'not supported' and 'pending review' are the expected outcomes of every
    # vacancy in this build — and 'pending review' stays expected afterwards,
    # since --all never auto-submits. Neither may make a normal run look broken.
    # Only real failures do.
    if counts["failed"]:
        sys.exit(1)


def cmd_submit(args, settings) -> None:
    db_path = Path(settings.DB_PATH)

    if args.all:
        _submit_all(args.manual, db_path)
        return

    conn = init_vacancy_db(db_path)
    try:
        vacancy = get_by_id(conn, args.vacancy_id)
    finally:
        conn.close()

    if vacancy is None:
        print(f"Error: no vacancy found with ID {args.vacancy_id}")
        sys.exit(1)

    attempt = submit_one(vacancy, args.manual, db_path)
    if attempt is None or attempt.outcome == SubmissionOutcome.FAILED:
        sys.exit(1)
