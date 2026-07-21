"""RED: src/doc_gen/cv_generator.py and cover_letter_generator.py don't
exist yet — these imports must fail first. Fresh OFFLINE_MODE stub
branches per ADR-003 §3, §7 — unlike the sibling projects, there is no
pre-existing offline branch to preserve here; both are new."""

from unittest.mock import patch

from src.doc_gen.cover_letter_generator import generate_cover_letter
from src.doc_gen.cv_generator import generate_cv
from src.doc_gen.runner import RunnerResult
from src.doc_gen.schema import GenerationResult, GenerationStatus
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane
from src.vacancy_search.schema import Vacancy


def _profile(**overrides) -> CandidateProfile:
    defaults = dict(
        name="Tebello Lelosa",
        region="Gauteng, South Africa",
        skills=["Operations management", "Lean manufacturing", "Supply chain"],
        experience=[
            ExperienceEntry(
                title="Operations Foreman",
                company="FanMovement (Pty) Ltd",
                start_date="2020-01",
            )
        ],
        target_titles=[TitleLane(title="Operations Foreman", primary=True)],
        industries=["Manufacturing"],
    )
    defaults.update(overrides)
    return CandidateProfile(**defaults)


def _vacancy(**overrides) -> Vacancy:
    defaults = dict(
        company="Acme Engineering",
        title="Operations Foreman",
        url="https://za.indeed.com/viewjob?jk=abc123",
        description="Oversee workshop production.",
    )
    defaults.update(overrides)
    return Vacancy(**defaults)


class TestGenerateCvOffline:
    def test_offline_mode_returns_stub_without_runner_call(self):
        with patch("src.doc_gen.cv_generator.run_claude_code") as mock_runner:
            result = generate_cv(_profile(), _vacancy())

        mock_runner.assert_not_called()
        assert isinstance(result, GenerationResult)
        assert result.doc_type == "cv"
        assert result.status == GenerationStatus.SUCCESS
        assert result.content
        assert "Tebello Lelosa" in result.content

    def test_offline_stub_is_deterministic(self):
        first = generate_cv(_profile(), _vacancy())
        second = generate_cv(_profile(), _vacancy())

        assert first.content == second.content


class TestGenerateCvOnline:
    def test_non_offline_routes_through_runner(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        with patch(
            "src.doc_gen.cv_generator.run_claude_code",
            return_value=RunnerResult(
                status=GenerationStatus.SUCCESS,
                result_text="# Tailored CV",
                session_id="sess-1",
                duration_ms=1000,
                cost_usd=0.01,
            ),
        ) as mock_runner:
            result = generate_cv(_profile(), _vacancy())

        mock_runner.assert_called_once()
        assert result.status == GenerationStatus.SUCCESS
        assert result.content == "# Tailored CV"
        assert result.session_id == "sess-1"
        assert result.duration_ms == 1000
        assert result.cost_usd == 0.01

    def test_throttled_result_propagates_from_runner(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        with patch(
            "src.doc_gen.cv_generator.run_claude_code",
            return_value=RunnerResult(
                status=GenerationStatus.THROTTLED,
                error_message="rate limit exceeded",
            ),
        ):
            result = generate_cv(_profile(), _vacancy())

        assert result.status == GenerationStatus.THROTTLED
        assert result.content is None
        assert result.error_message == "rate limit exceeded"

    def test_error_result_propagates_from_runner(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        with patch(
            "src.doc_gen.cv_generator.run_claude_code",
            return_value=RunnerResult(
                status=GenerationStatus.ERROR,
                error_message="something broke",
            ),
        ):
            result = generate_cv(_profile(), _vacancy())

        assert result.status == GenerationStatus.ERROR
        assert result.error_message == "something broke"


class TestGenerateCoverLetterOffline:
    def test_offline_mode_returns_stub_without_runner_call(self):
        with patch(
            "src.doc_gen.cover_letter_generator.run_claude_code"
        ) as mock_runner:
            result = generate_cover_letter(_profile(), _vacancy())

        mock_runner.assert_not_called()
        assert result.doc_type == "cover_letter"
        assert result.status == GenerationStatus.SUCCESS
        assert result.content
        assert "Acme Engineering" in result.content

    def test_offline_stub_is_deterministic(self):
        first = generate_cover_letter(_profile(), _vacancy())
        second = generate_cover_letter(_profile(), _vacancy())

        assert first.content == second.content


class TestGenerateCoverLetterOnline:
    def test_non_offline_routes_through_runner(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        with patch(
            "src.doc_gen.cover_letter_generator.run_claude_code",
            return_value=RunnerResult(
                status=GenerationStatus.SUCCESS,
                result_text="Dear Hiring Manager,",
                session_id="sess-2",
                duration_ms=800,
                cost_usd=0.008,
            ),
        ) as mock_runner:
            result = generate_cover_letter(_profile(), _vacancy())

        mock_runner.assert_called_once()
        assert result.status == GenerationStatus.SUCCESS
        assert result.content == "Dear Hiring Manager,"

    def test_error_result_propagates_from_runner(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        with patch(
            "src.doc_gen.cover_letter_generator.run_claude_code",
            return_value=RunnerResult(
                status=GenerationStatus.ERROR,
                error_message="something broke",
            ),
        ):
            result = generate_cover_letter(_profile(), _vacancy())

        assert result.status == GenerationStatus.ERROR
        assert result.error_message == "something broke"
