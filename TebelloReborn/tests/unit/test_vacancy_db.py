"""RED: src/vacancy_search/db.py doesn't exist yet — these imports must fail first."""

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
