"""RED: src/matching/pipeline.py doesn't exist yet — these imports must
fail first."""

from unittest.mock import patch

import pytest

from src.matching.pipeline import run_matching
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane
from src.vacancy_search.db import (
    get_by_id,
    init_db,
    insert_vacancy,
    update_vacancy_status,
)
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


def _mock_score():
    return (78, ["Strong ops background"], ["No Eskom outage experience"], "Apply")


def _seeded_vacancy(db_path):
    conn = init_db(db_path)
    vacancy_id = insert_vacancy(
        conn, Vacancy(company="Acme", title="Operations Foreman", url="https://x")
    )
    vacancy = get_by_id(conn, vacancy_id)
    conn.close()
    return vacancy_id, vacancy


class TestRunMatching:
    @patch("src.matching.pipeline.score_vacancy")
    def test_transitions_new_to_scored_and_persists_result(self, mock_score, tmp_path):
        mock_score.return_value = _mock_score()
        db_path = tmp_path / "career.db"
        vacancy_id, vacancy = _seeded_vacancy(db_path)

        result = run_matching(vacancy, _profile(), db_path=db_path)

        assert result.status == "scored"
        assert result.score == 78

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()

        assert reloaded.status == "scored"
        assert reloaded.score == 78
        assert reloaded.strengths == ["Strong ops background"]
        assert reloaded.weaknesses == ["No Eskom outage experience"]
        assert reloaded.recommendation == "Apply"

    @patch("src.matching.pipeline.score_vacancy")
    def test_invalid_current_status_raises(self, mock_score, tmp_path):
        mock_score.return_value = _mock_score()
        db_path = tmp_path / "career.db"
        vacancy_id, _ = _seeded_vacancy(db_path)

        conn = init_db(db_path)
        update_vacancy_status(conn, vacancy_id, "scored")  # already scored
        vacancy = get_by_id(conn, vacancy_id)
        conn.close()

        with pytest.raises(ValueError, match="Invalid transition"):
            run_matching(vacancy, _profile(), db_path=db_path)

    @patch("src.matching.pipeline.score_vacancy")
    def test_calls_scorer_with_profile_and_vacancy(self, mock_score, tmp_path):
        mock_score.return_value = _mock_score()
        db_path = tmp_path / "career.db"
        _, vacancy = _seeded_vacancy(db_path)
        profile = _profile()

        run_matching(vacancy, profile, db_path=db_path)

        mock_score.assert_called_once_with(profile, vacancy)

    @patch("src.matching.pipeline.score_vacancy")
    def test_no_partial_write_on_invalid_transition(self, mock_score, tmp_path):
        """If the status transition is invalid, the match result must not
        be persisted either — no half-applied state."""
        mock_score.return_value = _mock_score()
        db_path = tmp_path / "career.db"
        vacancy_id, _ = _seeded_vacancy(db_path)

        conn = init_db(db_path)
        update_vacancy_status(conn, vacancy_id, "scored")
        vacancy = get_by_id(conn, vacancy_id)
        conn.close()

        with pytest.raises(ValueError):
            run_matching(vacancy, _profile(), db_path=db_path)

        conn = init_db(db_path)
        reloaded = get_by_id(conn, vacancy_id)
        conn.close()

        assert reloaded.score is None
