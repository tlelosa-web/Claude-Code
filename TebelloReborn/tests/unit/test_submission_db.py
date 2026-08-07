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

from src.submission.db import get_attempts_for_vacancy, init_db, save_attempt
from src.submission.schema import SubmissionAttempt, SubmissionMethod, SubmissionOutcome
from src.vacancy_search.db import init_db as init_vacancy_db, insert_vacancy
from src.vacancy_search.schema import Vacancy


def _seed_vacancy(db_path) -> int:
    conn = init_vacancy_db(db_path)
    vacancy_id = insert_vacancy(
        conn, Vacancy(company="Acme", title="Operations Foreman", url="https://x")
    )
    conn.close()
    return vacancy_id


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

    def test_records_nothing_in_the_migration_ledger(self, tmp_path):
        """This module owns no migrations — `submissions` is a net-new table
        created directly in init_db(), which needs none (spec §Migration Note).

        Converted from `test_does_not_advance_user_version` per ADR-004's
        Consequences: the counter it guarded is frozen, and the equivalent
        assertion is that this module writes no ledger rows and disturbs no
        other module's. Note the original reason for having no migrations.py at
        all is now gone — under the ledger, versions are per-module, so Phase B
        can add one starting at 1."""
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
        submission_rows = [row for row in after if row[0] == "submission"]
        conn.close()

        assert submission_rows == []
        assert after == before


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
