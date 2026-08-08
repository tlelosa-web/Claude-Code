import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from .migrations import apply_migrations
from .schema import (
    FieldType,
    PrepReadiness,
    PrepStatus,
    QuestionDecision,
    ScreeningQuestion,
    Sensitivity,
    SubmissionAttempt,
    SubmissionMethod,
    SubmissionOutcome,
    SubmissionPrep,
)

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "career.db"

# `submission_preps` and `screening_questions` are net-new tables, so their
# CREATE TABLE statements live here rather than in migrations.py (Hard Rule 6).
# What *is* in migrations.py is the one real schema change Phase B makes:
# widening `submissions.outcome` to accept `pending_review`.


class SubmissionSchemaDriftError(Exception):
    """The stored `submissions` DDL doesn't accept every SubmissionOutcome.

    Spec Amendment A4. `CREATE TABLE IF NOT EXISTS` is a no-op against an
    existing table, so a database that ran `submit` before Phase B keeps its old
    3-value constraint no matter what the DDL string here says. The migration
    normally fixes that; this guard catches the cases it can't reach — a
    restored backup, a hand-edited schema, a ledger row without the DDL change
    it claims. Failing at init with a named error beats failing at insert with a
    CHECK violation, a long way from the code that caused it.
    """


def _attempt_from_row(row: sqlite3.Row) -> SubmissionAttempt:
    return SubmissionAttempt(
        id=row["id"],
        vacancy_id=row["vacancy_id"],
        method=SubmissionMethod(row["method"]),
        outcome=SubmissionOutcome(row["outcome"]),
        detail=row["detail"],
        attempted_at=row["attempted_at"],
    )


def _prep_from_row(row: sqlite3.Row) -> SubmissionPrep:
    return SubmissionPrep(
        id=row["id"],
        vacancy_id=row["vacancy_id"],
        status=PrepStatus(row["status"]),
        detail=row["detail"],
        step_url=row["step_url"],
        prepped_at=row["prepped_at"],
    )


def _question_from_row(row: sqlite3.Row) -> ScreeningQuestion:
    options = json.loads(row["options_json"]) if row["options_json"] else None
    return ScreeningQuestion(
        id=row["id"],
        vacancy_id=row["vacancy_id"],
        prep_id=row["prep_id"],
        question_text=row["question_text"],
        field_type=FieldType(row["field_type"]),
        field_key=row["field_key"],
        required=bool(row["required"]),
        options=options,
        step_url=row["step_url"],
        position=row["position"],
        fingerprint=row["fingerprint"],
        sensitivity=Sensitivity(row["sensitivity"]),
        drafted_answer=row["drafted_answer"],
        final_answer=row["final_answer"],
        decision=QuestionDecision(row["decision"]),
        extracted_at=row["extracted_at"],
        decided_at=row["decided_at"],
    )


def _assert_outcome_check_current(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='submissions'"
    ).fetchone()
    if row is None:
        return
    missing = sorted(o.value for o in SubmissionOutcome if o.value not in row[0])
    if missing:
        raise SubmissionSchemaDriftError(
            f"submissions.outcome does not accept {missing}. The stored schema "
            f"predates this build and the migration did not reach it. Rebuild the "
            f"table (see src/submission/migrations.py) or restore a database whose "
            f"schema matches."
        )


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Per-connection in SQLite, not a property of the schema — it has to be set
    # on every connection that writes, which is why save_attempt's callers get
    # their connection from here and nowhere else.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
            method TEXT NOT NULL CHECK (method IN ('auto','manual')),
            outcome TEXT NOT NULL CHECK (outcome IN ('submitted','failed','not_supported','pending_review')),
            detail TEXT,
            attempted_at TEXT NOT NULL
        )
    """)
    # Append-only, like submissions and approvals: a failed prep followed by a
    # successful re-prep is the ordinary path, so several rows per vacancy are
    # expected and get_latest_prep() resolves the multiplicity.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submission_preps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
            status TEXT NOT NULL CHECK (status IN (
                'questions_extracted','no_questions','external_ats',
                'captcha_detected','session_expired','unsupported_form','error')),
            detail TEXT,
            step_url TEXT,
            prepped_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS screening_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
            prep_id INTEGER NOT NULL REFERENCES submission_preps(id),
            question_text TEXT NOT NULL,
            field_type TEXT NOT NULL CHECK (field_type IN (
                'text','textarea','select','checkbox','radio','file')),
            field_key TEXT,
            required INTEGER NOT NULL DEFAULT 0,
            options_json TEXT,
            step_url TEXT NOT NULL,
            position INTEGER NOT NULL,
            fingerprint TEXT NOT NULL,
            sensitivity TEXT NOT NULL DEFAULT 'ordinary' CHECK (sensitivity IN (
                'ordinary','compensation','work_authorization','demographic')),
            drafted_answer TEXT,
            final_answer TEXT,
            decision TEXT NOT NULL DEFAULT 'pending' CHECK (decision IN (
                'pending','approved','edited','rejected')),
            extracted_at TEXT NOT NULL,
            decided_at TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_submission_preps_vacancy "
        "ON submission_preps(vacancy_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_screening_questions_prep "
        "ON screening_questions(prep_id)"
    )
    conn.commit()
    apply_migrations(conn)
    # After the migration, never before: on a database that ran `submit` before
    # Phase B, the widening is what makes this pass.
    _assert_outcome_check_current(conn)
    return conn


def save_attempt(conn: sqlite3.Connection, attempt: SubmissionAttempt) -> int:
    """Persist one submission attempt. Append-only — several rows per vacancy
    are expected (a `not_supported` followed later by a manual submission is the
    ordinary path in this build)."""
    cursor = conn.execute(
        """
        INSERT INTO submissions
            (vacancy_id, method, outcome, detail, attempted_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            attempt.vacancy_id,
            attempt.method.value,
            attempt.outcome.value,
            attempt.detail,
            attempt.attempted_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_attempts_for_vacancy(
    conn: sqlite3.Connection, vacancy_id: int
) -> List[SubmissionAttempt]:
    """Newest first. `vacancies.status` is current state; this is history — a
    reader must not treat an older `not_supported` row as the current one."""
    rows = conn.execute(
        "SELECT * FROM submissions WHERE vacancy_id = ? ORDER BY id DESC",
        (vacancy_id,),
    ).fetchall()
    return [_attempt_from_row(r) for r in rows]


def save_prep(conn: sqlite3.Connection, prep: SubmissionPrep) -> int:
    """Persist one prep run. Append-only — a re-prep adds a row, never replaces
    one, so the history of why a vacancy stalled stays readable."""
    cursor = conn.execute(
        """
        INSERT INTO submission_preps
            (vacancy_id, status, detail, step_url, prepped_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            prep.vacancy_id,
            prep.status.value,
            prep.detail,
            prep.step_url,
            prep.prepped_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_latest_prep(
    conn: sqlite3.Connection, vacancy_id: int
) -> Optional[SubmissionPrep]:
    """The prep run that decides this vacancy's fate, or None if never prepped.

    Same ORDER BY id DESC LIMIT 1 shape as review/db.py's
    get_approval_by_vacancy_id — an older row is history, not current state.
    """
    row = conn.execute(
        "SELECT * FROM submission_preps WHERE vacancy_id = ? ORDER BY id DESC LIMIT 1",
        (vacancy_id,),
    ).fetchone()
    return None if row is None else _prep_from_row(row)


def save_question(conn: sqlite3.Connection, question: ScreeningQuestion) -> int:
    cursor = conn.execute(
        """
        INSERT INTO screening_questions
            (vacancy_id, prep_id, question_text, field_type, field_key, required,
             options_json, step_url, position, fingerprint, sensitivity,
             drafted_answer, final_answer, decision, extracted_at, decided_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            question.vacancy_id,
            question.prep_id,
            question.question_text,
            question.field_type.value,
            question.field_key,
            int(question.required),
            json.dumps(question.options) if question.options is not None else None,
            question.step_url,
            question.position,
            question.fingerprint,
            question.sensitivity.value,
            question.drafted_answer,
            question.final_answer,
            question.decision.value,
            question.extracted_at,
            question.decided_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_questions_for_prep(
    conn: sqlite3.Connection, prep_id: int
) -> List[ScreeningQuestion]:
    """Scoped to one prep run, in the form's own order.

    Keyed on prep_id rather than vacancy_id deliberately (A12): a re-prep's
    questions must never mix with a stale set, since re-extraction happens
    precisely when the form may have changed.
    """
    rows = conn.execute(
        "SELECT * FROM screening_questions WHERE prep_id = ? ORDER BY position, id",
        (prep_id,),
    ).fetchall()
    return [_question_from_row(r) for r in rows]


# Prep failures that a re-run can plausibly clear. EXTERNAL_ATS is the one that
# can't: it's a property of the posting, so it routes to submit-by-hand instead.
_RETRYABLE_PREP_FAILURES = frozenset(
    {
        PrepStatus.CAPTCHA_DETECTED,
        PrepStatus.SESSION_EXPIRED,
        PrepStatus.UNSUPPORTED_FORM,
        PrepStatus.ERROR,
    }
)

_RUN_PREP = "run `career-engine prep-submission --vacancy-id {vacancy_id}`"


def submission_prep_ready(conn: sqlite3.Connection, vacancy_id: int) -> PrepReadiness:
    """Whether this vacancy may proceed to an adapter's submit(), per A2's gate.

    Named for the whole question, not half of it: the earlier
    all_questions_reviewed() counted question decisions, which cannot tell
    "prep never ran" from "prepped and this posting genuinely has no questions"
    — both are zero rows, and only one of them is submittable.
    """
    prep = get_latest_prep(conn, vacancy_id)

    if prep is None:
        return PrepReadiness(
            ready=False,
            outcome=SubmissionOutcome.PENDING_REVIEW,
            reason="never prepped — " + _RUN_PREP.format(vacancy_id=vacancy_id),
        )

    if prep.status == PrepStatus.EXTERNAL_ATS:
        return PrepReadiness(
            ready=False,
            outcome=SubmissionOutcome.NOT_SUPPORTED,
            reason="this posting redirects to an external ATS — submit it by hand",
        )

    if prep.status in _RETRYABLE_PREP_FAILURES:
        return PrepReadiness(
            ready=False,
            outcome=SubmissionOutcome.PENDING_REVIEW,
            reason=f"last prep ended {prep.status.value} — "
            + _RUN_PREP.format(vacancy_id=vacancy_id),
        )

    if prep.status == PrepStatus.NO_QUESTIONS:
        return PrepReadiness(ready=True, outcome=None, reason="")

    questions = get_questions_for_prep(conn, prep.id)
    if not questions:
        # Prep claimed it extracted questions and stored none. Treating this as
        # NO_QUESTIONS would submit the form with its questions blank.
        return PrepReadiness(
            ready=False,
            outcome=SubmissionOutcome.PENDING_REVIEW,
            reason="prep recorded questions_extracted but stored no questions — "
            + _RUN_PREP.format(vacancy_id=vacancy_id),
        )

    undecided = [
        q
        for q in questions
        if q.decision in (QuestionDecision.PENDING, QuestionDecision.REJECTED)
    ]
    if undecided:
        return PrepReadiness(
            ready=False,
            outcome=SubmissionOutcome.PENDING_REVIEW,
            reason=f"{len(undecided)} of {len(questions)} screening questions still "
            f"need a decision — run `career-engine review-questions "
            f"--vacancy-id {vacancy_id}`",
        )

    return PrepReadiness(ready=True, outcome=None, reason="")
