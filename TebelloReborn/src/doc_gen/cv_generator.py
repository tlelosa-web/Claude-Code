import os

from src.profile.schema import CandidateProfile
from src.vacancy_search.schema import Vacancy

from .runner import run_claude_code, wrap_untrusted_text
from .schema import GenerationResult, GenerationStatus

DOC_TYPE = "cv"


def _stub_cv_text(profile: CandidateProfile, vacancy: Vacancy) -> str:
    experience_lines = "\n".join(
        f"- {entry.title}, {entry.company} ({entry.start_date} – {entry.end_date or 'present'})"
        for entry in profile.experience
    )
    return (
        f"# {profile.name} — Tailored CV\n\n"
        f"## Target Role: {vacancy.title} at {vacancy.company}\n\n"
        f"Region: {profile.region}\n\n"
        f"## Skills\n{', '.join(profile.skills)}\n\n"
        f"## Experience\n{experience_lines}\n"
    )


def _build_cv_instruction(profile: CandidateProfile, vacancy: Vacancy) -> str:
    lane = profile.primary_title
    experience_lines = "\n".join(
        f"- {entry.title} at {entry.company} ({entry.start_date} to {entry.end_date or 'present'}): "
        f"{entry.description}"
        for entry in profile.experience
    )
    return (
        f"Write a tailored CV for {profile.name}, based in {profile.region}, "
        f"applying for the {vacancy.title} role at {vacancy.company}.\n\n"
        f"Primary target lane: {lane.title}\n"
        f"Skills: {', '.join(profile.skills)}\n"
        f"Industries: {', '.join(profile.industries)}\n\n"
        f"Experience:\n{experience_lines}\n\n"
        f"Vacancy description:\n{wrap_untrusted_text(vacancy.description)}\n\n"
        "Produce the CV as clean markdown, ready to export to PDF."
    )


def generate_cv(profile: CandidateProfile, vacancy: Vacancy) -> GenerationResult:
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return GenerationResult(
            status=GenerationStatus.SUCCESS,
            doc_type=DOC_TYPE,
            content=_stub_cv_text(profile, vacancy),
        )

    instruction = _build_cv_instruction(profile, vacancy)
    result = run_claude_code(instruction)

    return GenerationResult(
        status=result.status,
        doc_type=DOC_TYPE,
        content=result.result_text,
        session_id=result.session_id,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        error_message=result.error_message,
    )
