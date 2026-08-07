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
from .prep import (
    PrepNotSupportedError,
    ProfileMissingError,
    SessionSetupRequiredError,
    run_prep,
)
from .schema import PrepStatus, SubmissionAttempt, SubmissionOutcome


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


# What the operator does next, per prep outcome. Keyed on status rather than
# built from prep.detail: the detail says what the browser saw, this says what
# Tebello should do about it, and collapsing the two is how "external ATS"
# ended up reading as "try again".
_PREP_NEXT_STEP: dict[PrepStatus, str] = {
    PrepStatus.QUESTIONS_EXTRACTED: (
        "run `career-engine review-questions --vacancy-id {vacancy_id}` to "
        "approve or edit each answer"
    ),
    PrepStatus.NO_QUESTIONS: (
        "this posting has no screening questions — it is ready to submit"
    ),
    PrepStatus.EXTERNAL_ATS: (
        "this posting hands off to an external ATS — submit it by hand"
    ),
    PrepStatus.CAPTCHA_DETECTED: (
        "a CAPTCHA challenge was showing — nothing was solved or clicked "
        "through. Submit this one by hand, or try prep again later"
    ),
    PrepStatus.SESSION_EXPIRED: (
        "the saved session expired mid-flow — re-run "
        "`python tools/indeed_login_setup.py`, then prep again"
    ),
    PrepStatus.UNSUPPORTED_FORM: (
        "the form's structure wasn't recognised — submit this one by hand"
    ),
    PrepStatus.ERROR: "prep failed — see the detail above, then try again",
}


def cmd_prep_submission(args, settings) -> None:
    """Read-only recon over one posting's apply form.

    Exits non-zero on anything that leaves the vacancy unsubmittable, so the
    command is usable in a shell chain. `no_questions` and `questions_extracted`
    are the only two successes, and only one of them is finished.
    """
    db_path = Path(settings.DB_PATH)

    conn = init_vacancy_db(db_path)
    try:
        vacancy = get_by_id(conn, args.vacancy_id)
    finally:
        conn.close()

    if vacancy is None:
        print(f"Error: no vacancy found with ID {args.vacancy_id}")
        sys.exit(1)

    print(f"Prepping vacancy {vacancy.id} ({vacancy.company} — {vacancy.title})")
    print(f"  {vacancy.url}\n")

    try:
        prep = run_prep(vacancy, db_path=db_path)
    except (
        SubmissionNotAllowedError,
        PrepNotSupportedError,
        SessionSetupRequiredError,
        ProfileMissingError,
    ) as exc:
        # Each of these is a precondition rather than a finding about the
        # posting, and prep deliberately records no row for any of them.
        print(f"  Refused: {exc}")
        sys.exit(1)

    print(f"  Result: {prep.status.value} — {prep.detail}")
    print(f"  Next: {_PREP_NEXT_STEP[prep.status].format(vacancy_id=vacancy.id)}")

    if prep.status not in (PrepStatus.QUESTIONS_EXTRACTED, PrepStatus.NO_QUESTIONS):
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
