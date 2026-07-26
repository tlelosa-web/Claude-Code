"""RED: src/review/db.py doesn't exist yet — these imports must fail
first. save_approval must actually persist a row — this is the exact bug
class ai-outreach-agency hit earlier (an unsaved approval), so the
regression guard is a fresh get_approval_by_vacancy_id call returning
the saved decision, not None."""

from src.review.db import get_approval_by_vacancy_id, init_db, save_approval
from src.review.schema import Decision, ReviewResult
from src.vacancy_search.db import init_db as init_vacancy_db, insert_vacancy
from src.vacancy_search.schema import Vacancy


def _seed_vacancy(db_path) -> int:
    conn = init_vacancy_db(db_path)
    vacancy_id = insert_vacancy(
        conn, Vacancy(company="Acme", title="Operations Foreman", url="https://x")
    )
    conn.close()
    return vacancy_id


class TestInitDb:
    def test_creates_approvals_table(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='approvals'"
        ).fetchall()
        assert len(tables) == 1
        conn.close()


class TestSaveApprovalPersistsAcrossConnections:
    def test_approved_decision_is_readable_after_fresh_connection(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_approval(
            conn, ReviewResult(vacancy_id=vacancy_id, decision=Decision.APPROVED)
        )
        conn.close()

        fresh_conn = init_db(db_path)
        result = get_approval_by_vacancy_id(fresh_conn, vacancy_id)
        fresh_conn.close()

        assert result is not None
        assert result.decision == Decision.APPROVED

    def test_edited_decision_persists_edited_text(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_approval(
            conn,
            ReviewResult(
                vacancy_id=vacancy_id,
                decision=Decision.EDITED,
                edited_cv_text="# Edited CV",
                edited_cover_letter_text="Edited letter",
            ),
        )
        conn.close()

        fresh_conn = init_db(db_path)
        result = get_approval_by_vacancy_id(fresh_conn, vacancy_id)
        fresh_conn.close()

        assert result.decision == Decision.EDITED
        assert result.edited_cv_text == "# Edited CV"
        assert result.edited_cover_letter_text == "Edited letter"

    def test_get_approval_by_vacancy_id_returns_none_when_absent(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        result = get_approval_by_vacancy_id(conn, vacancy_id)
        conn.close()

        assert result is None

    def test_most_recent_decision_wins_on_repeat_review(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)

        conn = init_db(db_path)
        save_approval(
            conn, ReviewResult(vacancy_id=vacancy_id, decision=Decision.REJECTED)
        )
        save_approval(
            conn, ReviewResult(vacancy_id=vacancy_id, decision=Decision.APPROVED)
        )
        conn.close()

        fresh_conn = init_db(db_path)
        result = get_approval_by_vacancy_id(fresh_conn, vacancy_id)
        fresh_conn.close()

        assert result.decision == Decision.APPROVED
