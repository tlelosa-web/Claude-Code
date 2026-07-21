"""RED: src/matching/prompt_builder.py and src/matching/scorer.py don't
exist yet — these imports must fail first."""

from unittest.mock import patch

import pytest

from src.matching.prompt_builder import build_match_prompt
from src.matching.scorer import score_vacancy
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane
from src.vacancy_search.schema import Vacancy


def _profile() -> CandidateProfile:
    return CandidateProfile(
        name="Tebello Lelosa",
        region="Gauteng, South Africa",
        skills=["Production Planning", "SOX Compliance"],
        experience=[
            ExperienceEntry(
                title="Operations Foreman",
                company="FanMovement (Pty) Ltd",
                start_date="2025-10",
            )
        ],
        target_titles=[
            TitleLane(title="Operations Foreman/Manager", primary=True, weight=1.0),
            TitleLane(title="Project Engineer (Mechanical)", primary=False, weight=0.6),
        ],
        industries=["Manufacturing"],
    )


def _vacancy() -> Vacancy:
    return Vacancy(
        company="Acme Engineering",
        title="Operations Foreman",
        url="https://za.indeed.com/viewjob?jk=1",
        description="Run daily workshop operations for an industrial equipment manufacturer.",
    )


class TestPromptBuilder:
    def test_prompt_references_both_lanes(self):
        prompt = build_match_prompt(_profile(), _vacancy())

        assert "Operations Foreman/Manager" in prompt
        assert "Project Engineer (Mechanical)" in prompt

    def test_prompt_marks_primary_lane_with_weighting_language(self):
        prompt = build_match_prompt(_profile(), _vacancy())

        assert "primary" in prompt.lower()
        assert "1.0" in prompt
        assert "0.6" in prompt

    def test_prompt_includes_vacancy_details(self):
        prompt = build_match_prompt(_profile(), _vacancy())

        assert "Acme Engineering" in prompt
        assert "Operations Foreman" in prompt


class TestScoreVacancy:
    def test_offline_mode_returns_deterministic_fixture(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        score, strengths, weaknesses, recommendation = score_vacancy(
            _profile(), _vacancy()
        )

        assert isinstance(score, int)
        assert strengths
        assert weaknesses
        assert recommendation

    @patch("src.matching.scorer.call_ollama")
    def test_parses_mocked_ollama_response(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = (
            '{"score": 85, "strengths": ["Strong regional fit"], '
            '"weaknesses": ["No prior Eskom outage work listed"], '
            '"recommendation": "Apply"}'
        )

        score, strengths, weaknesses, recommendation = score_vacancy(
            _profile(), _vacancy()
        )

        assert score == 85
        assert strengths == ["Strong regional fit"]
        assert weaknesses == ["No prior Eskom outage work listed"]
        assert recommendation == "Apply"
        mock_call_ollama.assert_called_once()

    @patch("src.matching.scorer.call_ollama")
    def test_malformed_response_raises(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = "not json"

        from src.matching.scorer import MatchParseError

        with pytest.raises(MatchParseError):
            score_vacancy(_profile(), _vacancy())

    @patch("src.matching.scorer.call_ollama")
    def test_missing_fields_in_response_raises(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = '{"score": 85}'

        from src.matching.scorer import MatchParseError

        with pytest.raises(MatchParseError):
            score_vacancy(_profile(), _vacancy())
