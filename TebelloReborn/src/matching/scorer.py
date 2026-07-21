import json
import os

from src.matching.ollama_client import call_ollama
from src.matching.prompt_builder import build_match_prompt
from src.profile.schema import CandidateProfile
from src.vacancy_search.schema import Vacancy

# Deterministic OFFLINE_MODE fixture — no Ollama call is ever made when set.
_OFFLINE_FIXTURE = {
    "score": 72,
    "strengths": [
        "Strong operations/manufacturing background",
        "Regional match (Gauteng)",
    ],
    "weaknesses": ["Limited direct experience with this specific commodity"],
    "recommendation": (
        "Worth applying — solid alignment with the primary "
        "Operations Foreman/Manager lane."
    ),
}


class MatchParseError(ValueError):
    """Raised when the Ollama response can't be parsed into a match result."""


def score_vacancy(
    profile: CandidateProfile, vacancy: Vacancy
) -> tuple[int, list[str], list[str], str]:
    """Pure scoring function — does not touch the DB. Fails loud on
    OllamaError/OllamaUnreachableError; no fallback backend (ADR-003 §2)."""
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        fixture = _OFFLINE_FIXTURE
        return (
            fixture["score"],
            list(fixture["strengths"]),
            list(fixture["weaknesses"]),
            fixture["recommendation"],
        )

    prompt = build_match_prompt(profile, vacancy)
    raw_response = call_ollama(prompt)

    try:
        parsed = json.loads(raw_response)
        score = int(parsed["score"])
        strengths = list(parsed["strengths"])
        weaknesses = list(parsed["weaknesses"])
        recommendation = str(parsed["recommendation"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise MatchParseError(
            f"Could not parse Ollama match response: {raw_response!r}"
        ) from exc

    return score, strengths, weaknesses, recommendation
