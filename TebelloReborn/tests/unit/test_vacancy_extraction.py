"""RED: src/vacancy_search/extraction_prompt.py and
src/vacancy_search/extractor.py don't exist yet — these imports must fail
first.

Phase 13 (preserved unchanged from the original spec's Phase 12) — the raw
page handed to extract_vacancy_fields() now originates from a
discovered/gated URL (Phase 12 above), not a hand-maintained seed URL, which
is invisible to this function's own contract.
"""

from unittest.mock import patch

import pytest

from src.vacancy_search.extraction_prompt import build_extraction_prompt
from src.vacancy_search.extractor import VacancyExtractionError, extract_vacancy_fields

RAW_PAGE = {
    "url": "https://www.careers24.com/jobs/vacancy-1001-operations-foreman-acme/",
    "title": "Operations Foreman - Acme Engineering",
    "text_content": (
        "Acme Engineering is hiring an Operations Foreman to run daily "
        "workshop production. Salary R50,000 CTC. Closing date 2026-09-15."
    ),
    "_source_mode": "live",
}

WELL_FORMED_RESPONSE = (
    '{"company": "Acme Engineering", "title": "Operations Foreman", '
    '"description": "Run daily workshop production.", '
    '"url": "https://www.careers24.com/jobs/vacancy-1001-operations-foreman-acme/", '
    '"salary": "R50,000 CTC", "deadline": "2026-09-15"}'
)


class TestBuildExtractionPrompt:
    def test_lists_all_required_output_keys(self):
        prompt = build_extraction_prompt(RAW_PAGE["text_content"], "careers24")

        for key in ("company", "title", "description", "url", "salary", "deadline"):
            assert key in prompt

    def test_includes_the_raw_page_text(self):
        prompt = build_extraction_prompt(RAW_PAGE["text_content"], "careers24")

        assert "Operations Foreman" in prompt
        assert "Acme Engineering" in prompt


class TestExtractVacancyFields:
    @patch("src.vacancy_search.extractor.call_ollama")
    def test_parses_well_formed_response(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = WELL_FORMED_RESPONSE

        fields = extract_vacancy_fields(RAW_PAGE, "careers24")

        assert fields["company"] == "Acme Engineering"
        assert fields["title"] == "Operations Foreman"
        assert fields["url"] == RAW_PAGE["url"]
        assert fields["salary"] == "R50,000 CTC"
        assert fields["deadline"] == "2026-09-15"
        mock_call_ollama.assert_called_once()

    @patch("src.vacancy_search.extractor.call_ollama")
    def test_non_json_response_raises(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = "not json at all"

        with pytest.raises(VacancyExtractionError):
            extract_vacancy_fields(RAW_PAGE, "careers24")

    @patch("src.vacancy_search.extractor.call_ollama")
    def test_missing_required_field_raises(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = (
            '{"title": "Operations Foreman", '
            '"url": "https://example.co.za/job1", "description": "x", '
            '"salary": null, "deadline": null}'
        )

        with pytest.raises(VacancyExtractionError):
            extract_vacancy_fields(RAW_PAGE, "careers24")

    @patch("src.vacancy_search.extractor.call_ollama")
    def test_empty_string_required_field_raises(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = (
            '{"company": "N/A", "title": "", '
            '"url": "unknown", "description": "x", '
            '"salary": null, "deadline": null}'
        )

        with pytest.raises(VacancyExtractionError):
            extract_vacancy_fields(RAW_PAGE, "careers24")

    def test_offline_mode_returns_fixture_without_calling_ollama(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        with patch("src.vacancy_search.extractor.call_ollama") as mock_call_ollama:
            fields = extract_vacancy_fields(RAW_PAGE, "careers24")

        mock_call_ollama.assert_not_called()
        for key in ("company", "title", "description", "url", "salary", "deadline"):
            assert key in fields
        assert fields["company"]
        assert fields["title"]
        assert fields["url"]

    @patch("src.vacancy_search.extractor.call_ollama")
    def test_multi_listing_looking_page_still_yields_one_vacancy(
        self, mock_call_ollama, monkeypatch
    ):
        """Contract test (Codex Review Follow-up amendment): one raw page =
        one Vacancy, always — even if the raw page's text superficially
        resembles multiple job listings, extract_vacancy_fields() returns
        exactly one dict, never a list."""
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        multi_listing_page = {
            **RAW_PAGE,
            "text_content": (
                "1. Operations Foreman at Acme Engineering. "
                "2. Project Engineer at Beta Power. "
                "3. Production Planner at Gamma Manufacturing."
            ),
        }
        mock_call_ollama.return_value = WELL_FORMED_RESPONSE

        fields = extract_vacancy_fields(multi_listing_page, "careers24")

        assert isinstance(fields, dict)
        assert fields["company"] == "Acme Engineering"
