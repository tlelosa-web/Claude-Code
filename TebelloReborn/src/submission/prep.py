"""`prep-submission` — the read-only recon pass over one posting's apply form.

Phase E of docs/specs/indeed-submit-adapter.md.

This module is to prep what `pipeline.py` is to submit: it owns the gate and all
persistence, and the adapter owns none of either. The adapter is handed a
vacancy and a session path, and returns a `PrepResult` describing what it saw.
Everything after that — classifying sensitivity, fingerprinting, drafting,
writing rows — happens here (B3).

**Prep never transitions vacancy status** (B2). Every outcome leaves the vacancy
exactly where it was; the gate in `pipeline.py` reads the prep row later and
decides what submit may do.

Network in two separate senses (A9): the adapter drives a real browser, and
drafting shells out to `claude -p`, which is a local subprocess but a
subscription-backed one. Neither makes this an offline command, and the spec's
original "local, network-optional" claim about drafting was wrong.
"""

import logging
from pathlib import Path
from typing import Optional

from src.profile.db import get_profile, init_db as init_profile_db
from src.vacancy_search.db import get_by_id, init_db as init_vacancy_db
from src.vacancy_search.schema import Vacancy

from .db import init_db as init_submission_db, save_prep, save_question
from .drafting import draft_answer
from .eligibility import get_adapter
from .pipeline import ELIGIBLE_STATUSES, SubmissionNotAllowedError
from .questions import classify_sensitivity, compute_fingerprint
from .schema import PrepResult, PrepStatus, ScreeningQuestion, SubmissionPrep
from .session import resolve_session_state_path, session_state_available

logger = logging.getLogger(__name__)


class PrepNotSupportedError(Exception):
    """No adapter claims this vacancy, so there is no apply flow to inspect."""


class SessionSetupRequiredError(Exception):
    """The one-time login setup has never been run on this machine."""


class ProfileMissingError(Exception):
    """No candidate profile — drafting has no facts to answer from."""


def _inspect(adapter, vacancy: Vacancy, session_state_path: Path) -> PrepResult:
    """Run the adapter's walkthrough, turning a crash into a recordable result.

    Same reasoning as `pipeline._decide()`'s adapter guard: an adapter bug is
    data, not a traceback in the operator's face. It also *must* leave a row —
    with none, `submission_prep_ready()` reports "never prepped" and sends
    Tebello to run the command that just failed, with no record of why.
    """
    try:
        return adapter.inspect_apply_flow(vacancy, session_state_path)
    except Exception as exc:
        logger.warning("Prep adapter raised for vacancy %s: %s", vacancy.id, exc)
        return PrepResult(status=PrepStatus.ERROR, detail=f"adapter raised: {exc}")


def _persist_questions(
    conn, vacancy: Vacancy, prep_id: int, result: PrepResult
) -> None:
    """Judge each observed control, then store it.

    The order is the point: classify first, and let the classification decide
    whether drafting is even attempted (A11). Drafting and then discarding would
    satisfy the same assertion about the stored row while breaking the actual
    guarantee — that a sensitive question is never sent anywhere at all.
    """
    profile_conn = init_profile_db(_conn_path_of(conn))
    try:
        profile = get_profile(profile_conn)
    finally:
        profile_conn.close()

    if profile is None:
        raise ProfileMissingError(
            "no candidate profile in the database — run "
            "`career-engine import-profile --file data/profile_seed.json` first"
        )

    for observed in result.questions:
        sensitivity = classify_sensitivity(observed.question_text)
        drafted = draft_answer(observed.question_text, sensitivity, profile, vacancy)

        save_question(
            conn,
            ScreeningQuestion(
                vacancy_id=vacancy.id,
                prep_id=prep_id,
                question_text=observed.question_text,
                field_type=observed.field_type,
                field_key=observed.field_key,
                required=observed.required,
                options=observed.options,
                step_url=observed.step_url,
                position=observed.position,
                fingerprint=compute_fingerprint(
                    observed.question_text,
                    observed.field_type,
                    observed.required,
                    observed.options,
                ),
                sensitivity=sensitivity,
                drafted_answer=drafted,
            ),
        )


def _conn_path_of(conn) -> Path:
    """The file a sqlite3 connection is attached to.

    `prep` opens three modules' tables and each module owns its own `init_db`;
    asking the connection where it points beats threading `db_path` through
    every helper and having one of them silently default to `career.db` while
    the rest use a test's tmp_path.
    """
    row = conn.execute("PRAGMA database_list").fetchone()
    return Path(row[2])


def run_prep(vacancy: Vacancy, *, db_path: Optional[Path] = None) -> SubmissionPrep:
    """Inspect one approved posting's apply form and record what was found.

    Raises rather than recording for the two conditions that are about this
    machine instead of the posting — no adapter, and no saved session. A prep
    row is a statement about a posting, and `submission_prep_ready()` builds its
    own operator instruction from the row's status rather than reading its
    detail, so a row saying `session_expired` would tell Tebello to re-run
    prep-submission when the fix is the login setup.
    """
    vacancy_conn = init_vacancy_db(db_path)
    try:
        current = get_by_id(vacancy_conn, vacancy.id)
        if current is None:
            raise ValueError(f"Vacancy {vacancy.id} not found")

        # B1: the same gate submit enforces, imported rather than re-declared.
        # Prep opens an authenticated browser against a real employer's form —
        # it is not a preview of a vacancy nobody has approved.
        if current.status not in ELIGIBLE_STATUSES:
            raise SubmissionNotAllowedError(
                f"Vacancy {current.id} has status '{current.status}' — only "
                f"{sorted(ELIGIBLE_STATUSES)} may be prepped. An application "
                "must pass the human approval gate first."
            )
    finally:
        vacancy_conn.close()

    adapter = get_adapter(current)
    if adapter is None:
        raise PrepNotSupportedError(
            f"no auto-submit adapter for platform '{current.platform}' — this "
            f"one is yours to submit by hand"
        )

    if not session_state_available():
        raise SessionSetupRequiredError(
            f"no saved browser session at {resolve_session_state_path()} — run "
            f"the one-time login setup first (python tools/indeed_login_setup.py)"
        )

    result = _inspect(adapter, current, resolve_session_state_path())

    conn = init_submission_db(db_path)
    try:
        prep = SubmissionPrep(
            vacancy_id=current.id,
            status=result.status,
            detail=result.detail,
            step_url=result.step_url,
        )
        prep.id = save_prep(conn, prep)

        # After the prep row, never before: the questions reference prep_id, and
        # a crash mid-drafting must leave a readable prep row rather than
        # orphaned questions. Same fails-closed ordering as run_submission's.
        if result.status is PrepStatus.QUESTIONS_EXTRACTED:
            _persist_questions(conn, current, prep.id, result)

        return prep
    finally:
        conn.close()
