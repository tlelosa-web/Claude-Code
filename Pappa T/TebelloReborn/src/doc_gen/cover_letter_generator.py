import os

from src.profile.schema import CandidateProfile
from src.vacancy_search.schema import Vacancy

from .runner import run_claude_code, wrap_untrusted_text
from .schema import GenerationResult, GenerationStatus

DOC_TYPE = "cover_letter"


def _stub_cover_letter_text(profile: CandidateProfile, vacancy: Vacancy) -> str:
    return (
        f"Dear Hiring Manager at {vacancy.company},\n\n"
        f"I am writing to apply for the {vacancy.title} role. With a background in "
        f"{', '.join(profile.skills[:2]) if profile.skills else 'operations'}, "
        f"I believe I would be a strong fit for this position.\n\n"
        f"Sincerely,\n{profile.name}\n"
    )


def _build_cover_letter_instruction(profile: CandidateProfile, vacancy: Vacancy) -> str:
    lane = profile.primary_title
    return (
        f"Write a tailored cover letter for {profile.name}, based in {profile.region}, "
        f"applying for the {vacancy.title} role at {vacancy.company}.\n\n"
        f"Primary target lane: {lane.title}\n"
        f"Skills: {', '.join(profile.skills)}\n"
        f"Industries: {', '.join(profile.industries)}\n\n"
        f"Vacancy description:\n{wrap_untrusted_text(vacancy.description)}\n\n"
        "Produce the cover letter as clean markdown, ready to export to PDF. "
        "Keep it to one page."
    )


def generate_cover_letter(profile: CandidateProfile, vacancy: Vacancy) -> GenerationResult:
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return GenerationResult(
            status=GenerationStatus.SUCCESS,
            doc_type=DOC_TYPE,
            content=_stub_cover_letter_text(profile, vacancy),
        )

    instruction = _build_cover_letter_instruction(profile, vacancy)
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
