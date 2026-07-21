"""RED: src/doc_gen/pipeline.py doesn't exist yet — these imports must
fail first."""

from unittest.mock import patch

import pytest

from src.doc_gen.db import get_by_vacancy_id, init_db as init_doc_gen_db
from src.doc_gen.pipeline import run_doc_gen
from src.doc_gen.schema import GenerationResult, GenerationStatus
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane
from src.vacancy_search.db import get_by_id, init_db, insert_vacancy, update_vacancy_status
from src.vacancy_search.schema import Vacancy


def _profile() -> CandidateProfile:
    return CandidateProfile(
        name="Tebello Lelosa",
        region="Gauteng, South Africa",
        skills=["Production Planning"],
        experience=[
            ExperienceEntry(
                title="Operations Foreman", company="FanMovement", start_date="2025-10"
            )
        ],
        target_titles=[TitleLane(title="Operations Foreman/Manager", primary=True)],
        industries=["Manufacturing"],
    )


def _seeded_vacancy(db_path, status="scored"):
    conn = init_db(db_path)
    vacancy_id = insert_vacancy(
        conn, Vacancy(company="Acme", title="Operations Foreman", url="https://x")
    )
    if status != "new":
        update_vacancy_status(conn, vacancy_id, status)
    vacancy = get_by_id(conn, vacancy_id)
    conn.close()
    return vacancy_id, vacancy


def _success_result(doc_type, content="content"):
    return GenerationResult(status=GenerationStatus.SUCCESS, doc_type=doc_type, content=content)


def _throttled_result(doc_type):
    return GenerationResult(
        status=GenerationStatus.THROTTLED,
        doc_type=doc_type,
        error_message="rate limit exceeded",
    )


class TestRunDocGenSuccess:
    @patch("src.doc_gen.pipeline.export_cover_letter_pdf")
    @patch("src.doc_gen.pipeline.export_cv_pdf")
    @patch("src.doc_gen.pipeline.generate_cover_letter")
    @patch("src.doc_gen.pipeline.generate_cv")
    def test_transitions_scored_to_asset_ready_on_full_success(
        self, mock_cv, mock_cl, mock_export_cv, mock_export_cl, tmp_path
    ):
        mock_cv.return_value = _success_result("cv")
        mock_cl.return_value = _success_result("cover_letter")
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        result = run_doc_gen(_profile(), vacancy, db_path=db_path)

        assert result.status == "asset_ready"

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "asset_ready"

    @patch("src.doc_gen.pipeline.export_cover_letter_pdf")
    @patch("src.doc_gen.pipeline.export_cv_pdf")
    @patch("src.doc_gen.pipeline.generate_cover_letter")
    @patch("src.doc_gen.pipeline.generate_cv")
    def test_exports_pdf_for_each_successful_document(
        self, mock_cv, mock_cl, mock_export_cv, mock_export_cl, tmp_path
    ):
        mock_cv.return_value = _success_result("cv", content="# CV")
        mock_cl.return_value = _success_result("cover_letter", content="Dear...")
        db_path = tmp_path / "career.db"
        _, vacancy = _seeded_vacancy(db_path)

        run_doc_gen(_profile(), vacancy, db_path=db_path)

        mock_export_cv.assert_called_once()
        mock_export_cl.assert_called_once()

    @patch("src.doc_gen.pipeline.export_cover_letter_pdf")
    @patch("src.doc_gen.pipeline.export_cv_pdf")
    @patch("src.doc_gen.pipeline.generate_cover_letter")
    @patch("src.doc_gen.pipeline.generate_cv")
    def test_logs_one_generation_log_entry_per_document(
        self, mock_cv, mock_cl, mock_export_cv, mock_export_cl, tmp_path
    ):
        mock_cv.return_value = _success_result("cv")
        mock_cl.return_value = _success_result("cover_letter")
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        run_doc_gen(_profile(), vacancy, db_path=db_path)

        conn = init_doc_gen_db(db_path)
        entries = get_by_vacancy_id(conn, vacancy_id)
        conn.close()

        assert len(entries) == 2
        assert {e.doc_type for e in entries} == {"cv", "cover_letter"}
        assert all(e.status == GenerationStatus.SUCCESS for e in entries)


class TestRunDocGenPartialFailure:
    @patch("src.doc_gen.pipeline.export_cover_letter_pdf")
    @patch("src.doc_gen.pipeline.export_cv_pdf")
    @patch("src.doc_gen.pipeline.generate_cover_letter")
    @patch("src.doc_gen.pipeline.generate_cv")
    def test_throttled_document_leaves_vacancy_at_scored(
        self, mock_cv, mock_cl, mock_export_cv, mock_export_cl, tmp_path
    ):
        mock_cv.return_value = _success_result("cv")
        mock_cl.return_value = _throttled_result("cover_letter")
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        result = run_doc_gen(_profile(), vacancy, db_path=db_path)

        assert result.status == "scored"
        mock_export_cl.assert_not_called()

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()
        assert reloaded.status == "scored"

    @patch("src.doc_gen.pipeline.export_cover_letter_pdf")
    @patch("src.doc_gen.pipeline.export_cv_pdf")
    @patch("src.doc_gen.pipeline.generate_cover_letter")
    @patch("src.doc_gen.pipeline.generate_cv")
    def test_failure_still_logs_generation_attempt(
        self, mock_cv, mock_cl, mock_export_cv, mock_export_cl, tmp_path
    ):
        mock_cv.return_value = _success_result("cv")
        mock_cl.return_value = _throttled_result("cover_letter")
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        run_doc_gen(_profile(), vacancy, db_path=db_path)

        conn = init_doc_gen_db(db_path)
        entries = get_by_vacancy_id(conn, vacancy_id)
        conn.close()

        cover_letter_entry = next(e for e in entries if e.doc_type == "cover_letter")
        assert cover_letter_entry.status == GenerationStatus.THROTTLED
        assert cover_letter_entry.error_message == "rate limit exceeded"


class TestRunDocGenInvalidTransition:
    @patch("src.doc_gen.pipeline.export_cover_letter_pdf")
    @patch("src.doc_gen.pipeline.export_cv_pdf")
    @patch("src.doc_gen.pipeline.generate_cover_letter")
    @patch("src.doc_gen.pipeline.generate_cv")
    def test_invalid_current_status_raises_before_generating(
        self, mock_cv, mock_cl, mock_export_cv, mock_export_cl, tmp_path
    ):
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path, status="new")

        with pytest.raises(ValueError, match="Invalid transition"):
            run_doc_gen(_profile(), vacancy, db_path=db_path)

        mock_cv.assert_not_called()
        mock_cl.assert_not_called()
