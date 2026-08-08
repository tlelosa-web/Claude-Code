"""RED: src/vacancy_search/db.py doesn't exist yet — these imports must fail first."""

import sqlite3

import pytest

from src.vacancy_search.db import (
    VALID_TRANSITIONS,
    get_by_id,
    get_by_status,
    init_db,
    insert_vacancy,
    update_vacancy_status,
)
from src.vacancy_search.schema import Vacancy


def _vacancy(**overrides) -> Vacancy:
    defaults = dict(
        company="FanMovement (Pty) Ltd",
        title="Operations Foreman",
        url="https://za.indeed.com/viewjob?jk=abc123",
        description="Oversee workshop production.",
        platform="indeed",
        salary="R45,000 - R60,000 CTC",
        deadline=None,
    )
    defaults.update(overrides)
    return Vacancy(**defaults)


class TestInitDb:
    def test_creates_vacancies_table(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vacancies'"
        ).fetchall()

        assert len(tables) == 1
        conn.close()


class TestInsertAndDedup:
    def test_insert_returns_new_id(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        vacancy_id = insert_vacancy(conn, _vacancy())

        assert vacancy_id is not None
        conn.close()

    def test_duplicate_company_title_url_ignored(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        first_id = insert_vacancy(conn, _vacancy())
        second_id = insert_vacancy(conn, _vacancy())

        count = conn.execute("SELECT COUNT(*) FROM vacancies").fetchone()[0]

        assert first_id is not None
        assert second_id is None
        assert count == 1
        conn.close()

    def test_different_url_is_not_a_duplicate(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        insert_vacancy(conn, _vacancy())
        insert_vacancy(conn, _vacancy(url="https://za.indeed.com/viewjob?jk=different"))

        count = conn.execute("SELECT COUNT(*) FROM vacancies").fetchone()[0]

        assert count == 2
        conn.close()


class TestGetByStatusAndId:
    def test_get_by_status_returns_matching_rows(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        insert_vacancy(conn, _vacancy())
        insert_vacancy(conn, _vacancy(url="https://za.indeed.com/viewjob?jk=other"))

        results = get_by_status(conn, "new")

        assert len(results) == 2
        assert all(v.status == "new" for v in results)
        conn.close()

    def test_get_by_id_round_trips(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())

        result = get_by_id(conn, vacancy_id)

        assert result is not None
        assert result.company == "FanMovement (Pty) Ltd"
        conn.close()

    def test_get_by_id_missing_returns_none(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        assert get_by_id(conn, 999) is None
        conn.close()


class TestStatusStateMachine:
    def test_valid_transitions_constant(self):
        assert VALID_TRANSITIONS == {
            "new": {"scored"},
            "scored": {"asset_ready"},
            "asset_ready": {"approved", "rejected"},
            "approved": {"submitted", "submission_failed"},
            "submission_failed": {"submitted", "submission_failed"},
            "submitted": set(),
            "rejected": set(),
        }

    def test_valid_transition_updates_status(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())

        update_vacancy_status(conn, vacancy_id, "scored")

        assert get_by_id(conn, vacancy_id).status == "scored"
        conn.close()

    def test_invalid_transition_raises(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())

        with pytest.raises(ValueError, match="Invalid transition"):
            update_vacancy_status(conn, vacancy_id, "approved")
        conn.close()

    def test_transition_on_missing_vacancy_raises(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        with pytest.raises(ValueError, match="not found"):
            update_vacancy_status(conn, 999, "scored")
        conn.close()


class TestSubmissionTransitions:
    """Stage 6. `submission_failed` is reachable ONLY from `approved`, which is
    what lets the submit gate admit it for retries without ever letting an
    unapproved application reach a submission path (CLAUDE.md Hard Rule 1,
    docs/specs/submission-core.md Amendment A1)."""

    def _advance_to(self, conn, status: str) -> int:
        vacancy_id = insert_vacancy(conn, _vacancy())
        for step in ("scored", "asset_ready", "approved"):
            update_vacancy_status(conn, vacancy_id, step)
            if step == status:
                return vacancy_id
        return vacancy_id

    def test_approved_to_submitted(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = self._advance_to(conn, "approved")

        update_vacancy_status(conn, vacancy_id, "submitted")

        assert get_by_id(conn, vacancy_id).status == "submitted"
        conn.close()

    def test_approved_to_submission_failed(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = self._advance_to(conn, "approved")

        update_vacancy_status(conn, vacancy_id, "submission_failed")

        assert get_by_id(conn, vacancy_id).status == "submission_failed"
        conn.close()

    def test_submission_failed_retries_to_submitted(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = self._advance_to(conn, "approved")
        update_vacancy_status(conn, vacancy_id, "submission_failed")

        update_vacancy_status(conn, vacancy_id, "submitted")

        assert get_by_id(conn, vacancy_id).status == "submitted"
        conn.close()

    def test_submission_failed_can_fail_again(self, tmp_path):
        """A retry that fails again must be representable — otherwise the
        second failure raises instead of being recorded."""
        conn = init_db(tmp_path / "career.db")
        vacancy_id = self._advance_to(conn, "approved")
        update_vacancy_status(conn, vacancy_id, "submission_failed")

        update_vacancy_status(conn, vacancy_id, "submission_failed")

        assert get_by_id(conn, vacancy_id).status == "submission_failed"
        conn.close()

    def test_submitted_is_terminal(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = self._advance_to(conn, "approved")
        update_vacancy_status(conn, vacancy_id, "submitted")

        with pytest.raises(ValueError, match="Invalid transition"):
            update_vacancy_status(conn, vacancy_id, "submission_failed")
        conn.close()

    @pytest.mark.parametrize("status", ["new", "scored", "asset_ready"])
    def test_no_pre_approval_status_reaches_submitted(self, tmp_path, status):
        """Hard Rule 1 expressed in the state machine: nothing reaches a
        submitted state without passing through the human approval gate."""
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())
        for step in ("scored", "asset_ready"):
            if get_by_id(conn, vacancy_id).status == status:
                break
            update_vacancy_status(conn, vacancy_id, step)

        with pytest.raises(ValueError, match="Invalid transition"):
            update_vacancy_status(conn, vacancy_id, "submitted")
        conn.close()

    def test_rejected_never_reaches_submitted(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())
        update_vacancy_status(conn, vacancy_id, "scored")
        update_vacancy_status(conn, vacancy_id, "asset_ready")
        update_vacancy_status(conn, vacancy_id, "rejected")

        with pytest.raises(ValueError, match="Invalid transition"):
            update_vacancy_status(conn, vacancy_id, "submitted")
        conn.close()


def _ledger(conn, module):
    """Versions recorded for `module` in ADR-004's schema_migrations ledger."""
    rows = conn.execute(
        "SELECT version FROM schema_migrations WHERE module = ?", (module,)
    )
    return {row[0] for row in rows}


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


MATCH_COLUMNS = {"score", "strengths", "weaknesses", "recommendation"}


class TestBaselineMatchColumns:
    """ADR-004 §6, confirmed by Tebello. The four match columns lived ONLY in
    migrations 1-4 — `CREATE TABLE vacancies` omitted them entirely. That is
    what turned the Phase 17 regression from cosmetic into a crash on every new
    install: once profile advanced the shared counter past 4, the migrations
    were skipped and the columns existed nowhere at all.

    Not strictly required for correctness once the ledger exists, but the ADR's
    premise is that schema state should be legible from the schema, and this
    was the one baseline provably wrong-shaped."""

    def test_baseline_declares_the_match_columns(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        assert MATCH_COLUMNS <= _columns(conn, "vacancies")
        conn.close()

    def test_fresh_database_records_migrations_one_to_four_as_applied(self, tmp_path):
        """§3's skip-and-record. The baseline supplies the columns, so 1-4 have
        no DDL to do — but they must still be recorded, or a later run would
        try to ADD COLUMN over the top of them."""
        conn = init_db(tmp_path / "career.db")

        assert _ledger(conn, "vacancy_search") == {1, 2, 3, 4}
        conn.close()

    def test_fresh_and_legacy_databases_converge_on_the_same_schema(self, tmp_path):
        """A legacy file reaches the columns through migrations 1-4; a fresh one
        gets them from the baseline. Both must end up identical, or the fix has
        simply moved the divergence somewhere new."""
        legacy_path = tmp_path / "legacy.db"
        legacy = sqlite3.connect(str(legacy_path))
        legacy.execute("""
            CREATE TABLE vacancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT DEFAULT '',
                platform TEXT NOT NULL,
                salary TEXT,
                deadline TEXT,
                scraped_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                UNIQUE(company, title, url)
            )
        """)
        legacy.execute("PRAGMA user_version = 4")
        legacy.commit()
        legacy.close()

        legacy_conn = init_db(legacy_path)
        fresh_conn = init_db(tmp_path / "fresh.db")

        assert _columns(legacy_conn, "vacancies") == _columns(fresh_conn, "vacancies")
        assert MATCH_COLUMNS <= _columns(legacy_conn, "vacancies")
        assert _ledger(legacy_conn, "vacancy_search") == {1, 2, 3, 4}
        legacy_conn.close()
        fresh_conn.close()

    def test_the_frozen_counter_is_left_alone(self, tmp_path):
        """§5: whatever value a database carries, it keeps. The live career.db
        stays at 4 forever, and it means nothing."""
        db_path = tmp_path / "career.db"
        seed = sqlite3.connect(str(db_path))
        seed.execute("PRAGMA user_version = 4")
        seed.commit()
        seed.close()

        conn = init_db(db_path)

        assert conn.execute("PRAGMA user_version").fetchone()[0] == 4
        conn.close()
