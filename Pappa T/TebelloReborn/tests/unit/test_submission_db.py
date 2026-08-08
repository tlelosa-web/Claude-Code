"""RED: src/submission/db.py doesn't exist yet — these imports must fail
first. Shape mirrors src/review/db.py (approvals): net-new table created
directly in init_db(), no migrations.py entry — see
docs/specs/submission-core.md §Migration Note for why that is correct here
and why this module deliberately has no migrations.py at all.

The foreign-key test asserts rejection on the connection save_attempt
actually uses. `PRAGMA foreign_keys` is per-connection in SQLite, so a test
that opens its own connection would pass while the constraint sits inert in
production (spec Amendment A4).
"""

import sqlite3

import pytest

from src.submission.db import (
    SubmissionSchemaDriftError,
    get_attempts_for_vacancy,
    get_latest_prep,
    get_questions_for_prep,
    init_db,
    save_attempt,
    save_prep,
    save_question,
    submission_prep_ready,
)
from src.submission.schema import (
    FieldType,
    PrepStatus,
    QuestionDecision,
    ScreeningQuestion,
    Sensitivity,
    SubmissionAttempt,
    SubmissionMethod,
    SubmissionOutcome,
    SubmissionPrep,
)
from src.vacancy_search.db import init_db as init_vacancy_db, insert_vacancy
from src.vacancy_search.schema import Vacancy

OLD_OUTCOME_CHECK = "'submitted','failed','not_supported'"


def _seed_vacancy(db_path) -> int:
    conn = init_vacancy_db(db_path)
    vacancy_id = insert_vacancy(
        conn, Vacancy(company="Acme", title="Operations Foreman", url="https://x")
    )
    conn.close()
    return vacancy_id


def _question(prep_id, vacancy_id, **overrides) -> ScreeningQuestion:
    kwargs = {
        "vacancy_id": vacancy_id,
        "prep_id": prep_id,
        "question_text": "Describe a recent project you led.",
        "field_type": FieldType.TEXTAREA,
        "step_url": "https://za.indeed.com/apply/questions",
        "position": 0,
        "fingerprint": "a" * 64,
    }
    kwargs.update(overrides)
    return ScreeningQuestion(**kwargs)


def _prepped(db_path, vacancy_id, status=PrepStatus.QUESTIONS_EXTRACTED) -> int:
    """Record one prep run and return its id."""
    conn = init_db(db_path)
    prep_id = save_prep(conn, SubmissionPrep(vacancy_id=vacancy_id, status=status))
    conn.close()
    return prep_id


def _attempt(vacancy_id, outcome=SubmissionOutcome.NOT_SUPPORTED, detail=None):
    return SubmissionAttempt(
        vacancy_id=vacancy_id,
        method=SubmissionMethod.AUTO,
        outcome=outcome,
        detail=detail,
    )


class TestInitDb:
    def test_creates_submissions_table(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='submissions'"
        ).fetchall()
        assert len(tables) == 1
        conn.close()

    def test_creates_submission_preps_table(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='submission_preps'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1

    def test_creates_screening_questions_table(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='screening_questions'"
        ).fetchall()
        conn.close()
        assert len(tables) == 1

    def test_records_its_own_version_1_and_disturbs_no_other_module(self, tmp_path):
        """Replaces `test_records_nothing_in_the_migration_ledger`, whose
        premise Phase B ends.

        That test asserted this module owns no migrations, correct while
        `submissions` was net-new and unchanged. Widening its outcome CHECK is a
        real schema change, and SQLite cannot alter a CHECK in place — it is the
        create/copy/drop/rename rebuild, which is exactly what ADR-004's runner
        was proven to carry (`TestPhaseBShapedRebuild`). Version 1 is correct
        here because versions are per-module under the ledger; `(submission, 1)`
        and `(vacancy_search, 1)` are different keys.
        """
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        vacancy_conn = init_vacancy_db(db_path)
        before = {
            (row[0], row[1])
            for row in vacancy_conn.execute(
                "SELECT module, version FROM schema_migrations"
            )
        }
        vacancy_conn.close()

        conn = init_db(db_path)
        after = {
            (row[0], row[1])
            for row in conn.execute("SELECT module, version FROM schema_migrations")
        }
        conn.close()

        assert ("submission", 1) in after
        assert after - before == {("submission", 1)}

    def test_is_idempotent_across_repeated_calls(self, tmp_path):
        """Every command in this project calls init_db(). A rebuild that ran
        twice, or a ledger that gained a second row, would be a real bug."""
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        init_db(db_path).close()
        conn = init_db(db_path)
        rows = conn.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE module = 'submission'"
        ).fetchone()[0]
        conn.close()

        assert rows == 1

    def test_outcome_check_accepts_pending_review_on_a_fresh_database(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_attempt(
            conn,
            _attempt(vacancy_id, SubmissionOutcome.PENDING_REVIEW, detail="run prep"),
        )
        attempts = get_attempts_for_vacancy(conn, vacancy_id)
        conn.close()

        assert attempts[0].outcome == SubmissionOutcome.PENDING_REVIEW

    def test_widens_an_existing_old_shape_table_and_preserves_its_rows(self, tmp_path):
        """The trap spec Amendment A4 names: `CREATE TABLE IF NOT EXISTS` is a
        no-op against a database where `submit` already ran once, so editing the
        inlined DDL alone would leave the old 3-value constraint in place and
        every pending_review insert would fail at runtime, far from the code
        that caused it. The migration is what actually closes it."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        legacy = sqlite3.connect(str(db_path))
        legacy.execute(f"""
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
                method TEXT NOT NULL CHECK (method IN ('auto','manual')),
                outcome TEXT NOT NULL CHECK (outcome IN ({OLD_OUTCOME_CHECK})),
                detail TEXT,
                attempted_at TEXT NOT NULL
            )
        """)
        legacy.execute(
            "INSERT INTO submissions "
            "(vacancy_id, method, outcome, detail, attempted_at) "
            "VALUES (?, 'auto', 'not_supported', 'no adapter', ?)",
            (vacancy_id, "2026-08-06T00:00:00+00:00"),
        )
        legacy.commit()
        legacy.close()

        conn = init_db(db_path)
        save_attempt(conn, _attempt(vacancy_id, SubmissionOutcome.PENDING_REVIEW))
        attempts = get_attempts_for_vacancy(conn, vacancy_id)
        conn.close()

        assert [a.outcome for a in attempts] == [
            SubmissionOutcome.PENDING_REVIEW,
            SubmissionOutcome.NOT_SUPPORTED,
        ]
        assert attempts[1].detail == "no adapter"

    def test_refuses_loudly_when_the_stored_ddl_is_stale(self, tmp_path):
        """The A4 drift guard. The migration above is what normally prevents
        this, so the guard is reached only if the ledger says version 1 ran
        while the stored DDL says otherwise — a hand-edited database, a restored
        backup, a partial merge. Failing at init with a named error beats
        failing at insert with a CHECK violation."""
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        legacy = sqlite3.connect(str(db_path))
        legacy.execute(f"""
            CREATE TABLE submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
                method TEXT NOT NULL CHECK (method IN ('auto','manual')),
                outcome TEXT NOT NULL CHECK (outcome IN ({OLD_OUTCOME_CHECK})),
                detail TEXT,
                attempted_at TEXT NOT NULL
            )
        """)
        legacy.execute(
            "INSERT INTO schema_migrations (module, version, applied_at) "
            "VALUES ('submission', 1, '2026-08-07T00:00:00+00:00')"
        )
        legacy.commit()
        legacy.close()

        with pytest.raises(SubmissionSchemaDriftError) as exc:
            init_db(db_path)

        assert "pending_review" in str(exc.value)


class TestSaveAttempt:
    def test_returns_row_id(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        attempt_id = save_attempt(conn, _attempt(vacancy_id))
        conn.close()

        assert attempt_id is not None
        assert attempt_id > 0

    def test_persists_across_connections(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_attempt(
            conn,
            _attempt(vacancy_id, SubmissionOutcome.FAILED, detail="form rejected"),
        )
        conn.close()

        fresh = init_db(db_path)
        attempts = get_attempts_for_vacancy(fresh, vacancy_id)
        fresh.close()

        assert len(attempts) == 1
        assert attempts[0].outcome == SubmissionOutcome.FAILED
        assert attempts[0].method == SubmissionMethod.AUTO
        assert attempts[0].detail == "form rejected"
        assert attempts[0].vacancy_id == vacancy_id
        assert attempts[0].id is not None

    def test_foreign_key_enforced_on_the_saving_connection(self, tmp_path):
        """PRAGMA foreign_keys is per-connection — assert on the one that
        actually writes, not a freshly opened one."""
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            save_attempt(conn, _attempt(vacancy_id=999))
        conn.close()

    def test_check_constraint_rejects_unknown_outcome(self, tmp_path):
        """The dataclass blocks this at construction; the DB must block it too,
        so a raw INSERT from anywhere can't write an unknown value."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO submissions "
                "(vacancy_id, method, outcome, detail, attempted_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    vacancy_id,
                    "auto",
                    "definitely_submitted",
                    None,
                    "2026-08-06T00:00:00+00:00",
                ),
            )
        conn.close()

    def test_check_constraint_rejects_unknown_method(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO submissions "
                "(vacancy_id, method, outcome, detail, attempted_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    vacancy_id,
                    "telepathy",
                    "submitted",
                    None,
                    "2026-08-06T00:00:00+00:00",
                ),
            )
        conn.close()


class TestGetAttemptsForVacancy:
    def test_returns_empty_list_when_none(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        attempts = get_attempts_for_vacancy(conn, vacancy_id)
        conn.close()

        assert attempts == []

    def test_returns_newest_first(self, tmp_path):
        """submissions is an append-only attempt log — several rows per vacancy
        are expected and ordering is how a reader finds the current one."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_attempt(conn, _attempt(vacancy_id, SubmissionOutcome.NOT_SUPPORTED))
        save_attempt(conn, _attempt(vacancy_id, SubmissionOutcome.SUBMITTED))
        attempts = get_attempts_for_vacancy(conn, vacancy_id)
        conn.close()

        assert len(attempts) == 2
        assert attempts[0].outcome == SubmissionOutcome.SUBMITTED
        assert attempts[1].outcome == SubmissionOutcome.NOT_SUPPORTED

    def test_scopes_to_the_requested_vacancy(self, tmp_path):
        db_path = tmp_path / "career.db"
        first = _seed_vacancy(db_path)

        vacancy_conn = init_vacancy_db(db_path)
        second = insert_vacancy(
            vacancy_conn, Vacancy(company="Beta", title="Planner", url="https://y")
        )
        vacancy_conn.close()

        conn = init_db(db_path)
        save_attempt(conn, _attempt(first))
        save_attempt(conn, _attempt(second))
        attempts = get_attempts_for_vacancy(conn, second)
        conn.close()

        assert len(attempts) == 1
        assert attempts[0].vacancy_id == second


class TestSavePrep:
    def test_returns_row_id(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        prep_id = save_prep(
            conn, SubmissionPrep(vacancy_id=vacancy_id, status=PrepStatus.NO_QUESTIONS)
        )
        conn.close()

        assert prep_id > 0

    def test_round_trips_every_field(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_prep(
            conn,
            SubmissionPrep(
                vacancy_id=vacancy_id,
                status=PrepStatus.EXTERNAL_ATS,
                detail="redirects to workday",
                step_url="https://za.indeed.com/viewjob?jk=abc",
            ),
        )
        conn.close()

        fresh = init_db(db_path)
        prep = get_latest_prep(fresh, vacancy_id)
        fresh.close()

        assert prep.status == PrepStatus.EXTERNAL_ATS
        assert prep.detail == "redirects to workday"
        assert prep.step_url == "https://za.indeed.com/viewjob?jk=abc"
        assert prep.vacancy_id == vacancy_id
        assert prep.id is not None

    def test_foreign_key_enforced_on_the_saving_connection(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            save_prep(
                conn, SubmissionPrep(vacancy_id=999, status=PrepStatus.NO_QUESTIONS)
            )
        conn.close()

    def test_check_constraint_rejects_unknown_status(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO submission_preps "
                "(vacancy_id, status, detail, step_url, prepped_at) "
                "VALUES (?, 'nearly_done', NULL, NULL, ?)",
                (vacancy_id, "2026-08-07T00:00:00+00:00"),
            )
        conn.close()


class TestGetLatestPrep:
    def test_returns_none_when_never_prepped(self, tmp_path):
        """The one state that genuinely is an absence (Amendment A2)."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        prep = get_latest_prep(conn, vacancy_id)
        conn.close()

        assert prep is None

    def test_returns_the_newest_of_several(self, tmp_path):
        """submission_preps is append-only — a failed prep followed by a
        successful re-prep is the ordinary path, and only the latest decides."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_prep(
            conn,
            SubmissionPrep(vacancy_id=vacancy_id, status=PrepStatus.CAPTCHA_DETECTED),
        )
        save_prep(
            conn,
            SubmissionPrep(vacancy_id=vacancy_id, status=PrepStatus.NO_QUESTIONS),
        )
        prep = get_latest_prep(conn, vacancy_id)
        conn.close()

        assert prep.status == PrepStatus.NO_QUESTIONS

    def test_scopes_to_the_requested_vacancy(self, tmp_path):
        db_path = tmp_path / "career.db"
        first = _seed_vacancy(db_path)

        vacancy_conn = init_vacancy_db(db_path)
        second = insert_vacancy(
            vacancy_conn, Vacancy(company="Beta", title="Planner", url="https://y")
        )
        vacancy_conn.close()

        conn = init_db(db_path)
        save_prep(
            conn, SubmissionPrep(vacancy_id=first, status=PrepStatus.NO_QUESTIONS)
        )
        prep = get_latest_prep(conn, second)
        conn.close()

        assert prep is None


class TestSaveQuestion:
    def test_round_trips_every_field(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        save_question(
            conn,
            _question(
                prep_id,
                vacancy_id,
                field_type=FieldType.SELECT,
                field_key="q_2",
                required=True,
                options=["Yes", "No"],
                sensitivity=Sensitivity.WORK_AUTHORIZATION,
                question_text="Are you authorised to work in South Africa?",
                position=2,
                fingerprint="b" * 64,
            ),
        )
        conn.close()

        fresh = init_db(db_path)
        [question] = get_questions_for_prep(fresh, prep_id)
        fresh.close()

        assert question.field_type == FieldType.SELECT
        assert question.field_key == "q_2"
        assert question.required is True
        assert question.options == ["Yes", "No"]
        assert question.sensitivity == Sensitivity.WORK_AUTHORIZATION
        assert question.position == 2
        assert question.fingerprint == "b" * 64
        assert question.decision == QuestionDecision.PENDING
        assert question.drafted_answer is None
        assert question.decided_at is None
        assert question.id is not None

    def test_free_text_question_round_trips_options_as_none(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        save_question(conn, _question(prep_id, vacancy_id))
        [question] = get_questions_for_prep(conn, prep_id)
        conn.close()

        assert question.options is None
        assert question.required is False

    def test_foreign_key_enforced_on_the_prep(self, tmp_path):
        """prep_id is what stops a re-prep's questions mixing with a stale set,
        so a question pointing at no prep at all must not be storable."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            save_question(conn, _question(999, vacancy_id))
        conn.close()

    def test_check_constraint_rejects_unknown_field_type(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO screening_questions "
                "(vacancy_id, prep_id, question_text, field_type, step_url, "
                "position, fingerprint, extracted_at) "
                "VALUES (?, ?, 'q', 'slider', 'https://x', 0, 'f', ?)",
                (vacancy_id, prep_id, "2026-08-07T00:00:00+00:00"),
            )
        conn.close()

    def test_check_constraint_rejects_unknown_decision(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO screening_questions "
                "(vacancy_id, prep_id, question_text, field_type, step_url, "
                "position, fingerprint, decision, extracted_at) "
                "VALUES (?, ?, 'q', 'text', 'https://x', 0, 'f', 'probably', ?)",
                (vacancy_id, prep_id, "2026-08-07T00:00:00+00:00"),
            )
        conn.close()

    def test_check_constraint_rejects_unknown_sensitivity(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO screening_questions "
                "(vacancy_id, prep_id, question_text, field_type, step_url, "
                "position, fingerprint, sensitivity, extracted_at) "
                "VALUES (?, ?, 'q', 'text', 'https://x', 0, 'f', 'spicy', ?)",
                (vacancy_id, prep_id, "2026-08-07T00:00:00+00:00"),
            )
        conn.close()


class TestGetQuestionsForPrep:
    def test_returns_empty_list_when_none(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id, PrepStatus.NO_QUESTIONS)

        conn = init_db(db_path)
        questions = get_questions_for_prep(conn, prep_id)
        conn.close()

        assert questions == []

    def test_orders_by_position(self, tmp_path):
        """Position is the form's own order — review-questions and the adapter
        both walk the questions in the order the employer asks them."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        save_question(
            conn, _question(prep_id, vacancy_id, position=1, question_text="second")
        )
        save_question(
            conn, _question(prep_id, vacancy_id, position=0, question_text="first")
        )
        questions = get_questions_for_prep(conn, prep_id)
        conn.close()

        assert [q.question_text for q in questions] == ["first", "second"]

    def test_a_reprep_set_never_mixes_with_the_stale_one(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        first_prep = _prepped(db_path, vacancy_id)
        second_prep = _prepped(db_path, vacancy_id)

        conn = init_db(db_path)
        save_question(
            conn, _question(first_prep, vacancy_id, question_text="stale question")
        )
        save_question(
            conn, _question(second_prep, vacancy_id, question_text="fresh question")
        )
        questions = get_questions_for_prep(conn, second_prep)
        conn.close()

        assert [q.question_text for q in questions] == ["fresh question"]


class TestSubmissionPrepReady:
    """Amendment A2's gate table, one test per row. Renamed from
    all_questions_reviewed() because that name described half the check."""

    def _ready(self, db_path, vacancy_id):
        conn = init_db(db_path)
        readiness = submission_prep_ready(conn, vacancy_id)
        conn.close()
        return readiness

    def _decide(self, db_path, prep_id, vacancy_id, decision, **overrides):
        conn = init_db(db_path)
        save_question(
            conn,
            _question(prep_id, vacancy_id, decision=decision, **overrides),
        )
        conn.close()

    def test_never_prepped_is_pending_review(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is False
        assert readiness.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "prep-submission" in readiness.reason

    def test_external_ats_is_not_supported(self, tmp_path):
        """The one prep failure that is a permanent property of the posting, not
        a retryable condition — so it routes to submit-by-hand, not re-prep."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        _prepped(db_path, vacancy_id, PrepStatus.EXTERNAL_ATS)

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is False
        assert readiness.outcome == SubmissionOutcome.NOT_SUPPORTED

    @pytest.mark.parametrize(
        "status",
        [
            PrepStatus.CAPTCHA_DETECTED,
            PrepStatus.SESSION_EXPIRED,
            PrepStatus.UNSUPPORTED_FORM,
            PrepStatus.ERROR,
        ],
    )
    def test_retryable_prep_failures_are_pending_review(self, tmp_path, status):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        _prepped(db_path, vacancy_id, status)

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is False
        assert readiness.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "prep-submission" in readiness.reason

    def test_no_questions_proceeds(self, tmp_path):
        """The distinction the whole table exists for: zero questions because
        prep ran and found none is submittable; zero because prep never ran is
        not. Both are zero screening_questions rows."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        _prepped(db_path, vacancy_id, PrepStatus.NO_QUESTIONS)

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is True
        assert readiness.outcome is None

    def test_all_questions_decided_proceeds(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)
        self._decide(db_path, prep_id, vacancy_id, QuestionDecision.APPROVED)
        self._decide(
            db_path,
            prep_id,
            vacancy_id,
            QuestionDecision.EDITED,
            position=1,
            fingerprint="c" * 64,
        )

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is True

    @pytest.mark.parametrize(
        "decision", [QuestionDecision.PENDING, QuestionDecision.REJECTED]
    )
    def test_an_undecided_question_blocks_with_review_questions(
        self, tmp_path, decision
    ):
        """Hard Rule 1's principle extended to new content — a rejected answer
        is as unsubmittable as an unreviewed one."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        prep_id = _prepped(db_path, vacancy_id)
        self._decide(db_path, prep_id, vacancy_id, QuestionDecision.APPROVED)
        self._decide(
            db_path, prep_id, vacancy_id, decision, position=1, fingerprint="c" * 64
        )

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is False
        assert readiness.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "review-questions" in readiness.reason

    def test_questions_extracted_with_no_rows_does_not_proceed(self, tmp_path):
        """A contradiction — prep claimed it extracted questions and stored
        none. Treating it as NO_QUESTIONS would submit a form with its questions
        blank, so it blocks and asks for a re-prep."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        _prepped(db_path, vacancy_id, PrepStatus.QUESTIONS_EXTRACTED)

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is False
        assert readiness.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "prep-submission" in readiness.reason

    def test_only_the_latest_preps_questions_count(self, tmp_path):
        """A re-prep after an unreviewed set must not inherit its decisions —
        the questions were re-extracted precisely because they may have
        changed."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        stale_prep = _prepped(db_path, vacancy_id)
        self._decide(db_path, stale_prep, vacancy_id, QuestionDecision.APPROVED)

        fresh_prep = _prepped(db_path, vacancy_id)
        self._decide(db_path, fresh_prep, vacancy_id, QuestionDecision.PENDING)

        readiness = self._ready(db_path, vacancy_id)

        assert readiness.ready is False
        assert "review-questions" in readiness.reason
