"""RED: src/review/cli.py doesn't exist yet — these imports must fail
first. Design reviewed and signed off per docs/todo.md's Phase 6
mandatory Reviewer gate (before this file was written): every branch
persists the decision (save_approval) BEFORE advancing vacancy status,
so a failure after persistence still leaves a recorded decision (fails
closed), never an approved vacancy with no decision on file (fails
open). Mirrors ai-outreach-agency/src/approval/cli.py's structure."""

from unittest.mock import patch

import pytest

from src.review.cli import run_review_gate
from src.review.db import get_approval_by_vacancy_id, init_db as init_review_db
from src.review.schema import Decision
from src.vacancy_search.db import get_by_id, init_db, insert_vacancy, update_vacancy_status
from src.vacancy_search.schema import Vacancy

CV_TEXT = "# Tebello Lelosa — CV"
COVER_LETTER_TEXT = "Dear Hiring Manager,"


def _seeded_vacancy(db_path, status="asset_ready"):
    conn = init_db(db_path)
    vacancy_id = insert_vacancy(
        conn, Vacancy(company="Acme", title="Operations Foreman", url="https://x")
    )
    if status in ("scored", "asset_ready", "approved"):
        update_vacancy_status(conn, vacancy_id, "scored")
    if status in ("asset_ready", "approved"):
        update_vacancy_status(conn, vacancy_id, "asset_ready")
    if status == "approved":
        update_vacancy_status(conn, vacancy_id, "approved")
    vacancy = get_by_id(conn, vacancy_id)
    conn.close()
    return vacancy_id, vacancy


def _fake_input(responses):
    it = iter(responses)
    return lambda _prompt="": next(it)


class TestApprove:
    def test_approve_persists_and_advances_status(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        result = run_review_gate(
            vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["a"]), db_path=db_path
        )

        assert result.decision == Decision.APPROVED

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "approved"

        review_conn = init_review_db(db_path)
        approval = get_approval_by_vacancy_id(review_conn, vacancy_id)
        review_conn.close()
        assert approval is not None
        assert approval.decision == Decision.APPROVED


class TestReject:
    def test_reject_persists_and_advances_status(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        result = run_review_gate(
            vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["r"]), db_path=db_path
        )

        assert result.decision == Decision.REJECTED

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "rejected"

        review_conn = init_review_db(db_path)
        approval = get_approval_by_vacancy_id(review_conn, vacancy_id)
        review_conn.close()
        assert approval is not None
        assert approval.decision == Decision.REJECTED


class TestEdit:
    @patch("src.review.cli._edit_text")
    def test_edit_persists_edited_text_and_approves(self, mock_edit, tmp_path):
        mock_edit.side_effect = ["# Edited CV", "Edited cover letter"]
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        result = run_review_gate(
            vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["e"]), db_path=db_path
        )

        assert result.decision == Decision.EDITED
        assert result.edited_cv_text == "# Edited CV"
        assert result.edited_cover_letter_text == "Edited cover letter"

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "approved"

        review_conn = init_review_db(db_path)
        approval = get_approval_by_vacancy_id(review_conn, vacancy_id)
        review_conn.close()
        assert approval.decision == Decision.EDITED
        assert approval.edited_cv_text == "# Edited CV"
        assert approval.edited_cover_letter_text == "Edited cover letter"


class TestQuit:
    @patch("src.review.cli.update_vacancy_status")
    @patch("src.review.cli.save_approval")
    @patch("src.review.cli.init_vacancy_db")
    def test_quit_raises_and_touches_nothing(
        self, mock_init_vacancy_db, mock_save_approval, mock_update_status, tmp_path
    ):
        db_path = tmp_path / "career.db"
        _, vacancy = _seeded_vacancy(db_path)

        with pytest.raises(SystemExit) as exc_info:
            run_review_gate(
                vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["q"]), db_path=db_path
            )

        assert exc_info.value.code == 0
        mock_init_vacancy_db.assert_not_called()
        mock_save_approval.assert_not_called()
        mock_update_status.assert_not_called()


class TestInvalidTransition:
    @patch("src.review.cli.save_approval")
    def test_vacancy_not_yet_scored_raises_with_zero_writes(self, mock_save_approval, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path, status="new")

        with pytest.raises(ValueError, match="Invalid transition"):
            run_review_gate(
                vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["a"]), db_path=db_path
            )

        mock_save_approval.assert_not_called()
        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "new"

    @patch("src.review.cli.save_approval")
    def test_already_approved_vacancy_raises_with_zero_writes(self, mock_save_approval, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path, status="approved")

        with pytest.raises(ValueError, match="Invalid transition"):
            run_review_gate(
                vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["a"]), db_path=db_path
            )

        mock_save_approval.assert_not_called()

    @patch("src.review.cli.save_approval")
    def test_missing_vacancy_raises_with_zero_writes(self, mock_save_approval, tmp_path):
        db_path = tmp_path / "career.db"
        init_db(db_path)  # ensure table exists, no vacancy inserted
        missing_vacancy = Vacancy(id=999, company="Ghost", title="Nobody", url="https://x")

        with pytest.raises(ValueError, match="not found"):
            run_review_gate(
                missing_vacancy,
                CV_TEXT,
                COVER_LETTER_TEXT,
                input_fn=_fake_input(["a"]),
                db_path=db_path,
            )

        mock_save_approval.assert_not_called()


class TestFailureOrdering:
    """Regression guard for the unsaved-approval bug class (Reviewer
    sign-off Finding 1): the decision must be durably persisted before
    the vacancy status advances, so a failure never leaves an approved
    vacancy with no recorded decision."""

    @patch("src.review.cli.save_approval")
    def test_save_approval_failure_leaves_status_unchanged(self, mock_save_approval, tmp_path):
        mock_save_approval.side_effect = RuntimeError("disk full")
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        with pytest.raises(RuntimeError):
            run_review_gate(
                vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["a"]), db_path=db_path
            )

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "asset_ready"

    @patch("src.review.cli.update_vacancy_status")
    def test_status_update_failure_after_persist_leaves_decision_durable(
        self, mock_update_status, tmp_path
    ):
        mock_update_status.side_effect = RuntimeError("disk full")
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        with pytest.raises(RuntimeError):
            run_review_gate(
                vacancy, CV_TEXT, COVER_LETTER_TEXT, input_fn=_fake_input(["a"]), db_path=db_path
            )

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "asset_ready"

        review_conn = init_review_db(db_path)
        approval = get_approval_by_vacancy_id(review_conn, vacancy_id)
        review_conn.close()
        assert approval is not None
        assert approval.decision == Decision.APPROVED
