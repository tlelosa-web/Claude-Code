import json
import os

from src.shared.ollama_client import call_ollama
from src.vacancy_search.extraction_prompt import build_extraction_prompt
from src.vacancy_search.schema import REQUIRED_FIELDS

# Deterministic OFFLINE_MODE fixture — no Ollama call is ever made when set.
_OFFLINE_FIXTURE = {
    "company": "Example Crawled Employer (Pty) Ltd",
    "title": "Example Extracted Vacancy",
    "description": "Deterministic offline extraction fixture — no real crawl or LLM call.",
    "url": "https://example.co.za/extracted-placeholder",
    "salary": None,
    "deadline": None,
}

_OUTPUT_KEYS = ("company", "title", "description", "url", "salary", "deadline")


class VacancyExtractionError(ValueError):
    """Raised when the Ollama extraction response can't be parsed into
    valid vacancy fields — malformed JSON, or a required field
    (company/title/url) missing or present-but-empty. Distinct from
    matching/scorer.py's MatchParseError: this is a malformed *LLM
    extraction of a scraped page*, not a malformed *match score* — a
    different domain, deliberately not reused across the two."""


def extract_vacancy_fields(raw_page: dict, platform: str) -> dict:
    """Turns one raw crawled job-detail page into Vacancy-shaped fields via
    src.shared.ollama_client.call_ollama() (its second consumer, post the
    ollama_client.py shared/ promotion). Strict validation: any parse
    failure or a missing/empty required field (Vacancy.REQUIRED_FIELDS —
    company/title/url) raises VacancyExtractionError; a malformed-but-valid
    "N/A"-style value is a factual-accuracy problem, out of scope for this
    shape-only validation (see docs/specs/pnet-careers24-coverage.md's Open
    Items).

    One raw page = one Vacancy, always — this function never returns a
    list, even if the page's text superficially resembles multiple
    listings (Codex Review Follow-up amendment's contract).
    """
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return dict(_OFFLINE_FIXTURE)

    prompt = build_extraction_prompt(raw_page.get("text_content", ""), platform)
    raw_response = call_ollama(prompt)

    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise VacancyExtractionError(
            f"Could not parse Ollama extraction response as JSON: {raw_response!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise VacancyExtractionError(
            f"Ollama extraction response was not a JSON object: {raw_response!r}"
        )

    for field in REQUIRED_FIELDS:
        value = parsed.get(field)
        if not value or not str(value).strip():
            raise VacancyExtractionError(
                f"Missing or empty required field '{field}' in extraction "
                f"response: {raw_response!r}"
            )

    return {key: parsed.get(key) for key in _OUTPUT_KEYS}
