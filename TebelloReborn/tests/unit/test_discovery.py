"""RED: src/vacancy_search/discovery.py doesn't exist yet — these imports
must fail first.

Amendment — Automated Discovery Redesign (2026-07-29): discovery.py builds
platform search URLs, parses individual job-detail-page URLs out of a
listing page's raw text (a deterministic parse, never an LLM call — judgment
call #1), and gates PNet behind a manual-verification config, falling back
to the pre-existing data/crawler_seed_urls.json for PNet only.
"""

from unittest.mock import patch

from src.vacancy_search.discovery import (
    build_search_url,
    discover_job_urls,
    parse_job_urls_from_listing,
)

CAREERS24_LISTING_FIXTURE = """
<html><body>
<nav><a href="https://www.careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/">Search</a></nav>
<div class="results">
  <a href="https://www.careers24.com/jobs/vacancy-1001-operations-foreman-acme/">
    Operations Foreman - Acme Engineering
  </a>
  <a href="https://www.careers24.com/jobs/vacancy-1002-project-engineer-beta/">
    Project Engineer (Mechanical) - Beta Power
  </a>
</div>
<footer><a href="/privacy-policy">Privacy</a></footer>
</body></html>
"""


class TestBuildSearchUrlCareers24:
    def test_returns_confirmed_live_shape(self):
        url = build_search_url("careers24", "Operations Foreman", "Gauteng")

        assert (
            url
            == "https://www.careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/"
        )

    def test_slugifies_spaces_to_hyphens_and_lowercases(self):
        url = build_search_url("careers24", "Project Engineer (Mechanical)", "Gauteng")

        assert "kw-project-engineer-(mechanical)" in url


class TestParseJobUrlsFromListingCareers24:
    def test_extracts_individual_job_detail_urls(self):
        urls = parse_job_urls_from_listing(CAREERS24_LISTING_FIXTURE, "careers24")

        assert (
            "https://www.careers24.com/jobs/vacancy-1001-operations-foreman-acme/"
            in urls
        )
        assert (
            "https://www.careers24.com/jobs/vacancy-1002-project-engineer-beta/" in urls
        )

    def test_does_not_include_the_listing_search_url_itself(self):
        urls = parse_job_urls_from_listing(CAREERS24_LISTING_FIXTURE, "careers24")

        assert (
            "https://www.careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/"
            not in urls
        )

    def test_unknown_platform_returns_empty_list(self):
        urls = parse_job_urls_from_listing(CAREERS24_LISTING_FIXTURE, "glassdoor")

        assert urls == []


class TestDiscoverJobUrlsCareers24:
    @patch("src.vacancy_search.discovery.crawler_client.fetch_raw_page")
    def test_fetches_listing_then_parses_job_urls(
        self, mock_fetch_raw_page, monkeypatch
    ):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_fetch_raw_page.return_value = {
            "url": "https://www.careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/",
            "title": "Careers24 Search Results",
            "text_content": CAREERS24_LISTING_FIXTURE,
            "_source_mode": "live",
        }

        urls = discover_job_urls("careers24", limit=25)

        mock_fetch_raw_page.assert_called_once()
        called_url = mock_fetch_raw_page.call_args.args[0]
        assert "careers24.com/jobs/lc-" in called_url
        assert len(urls) == 2
        assert all(u["_source_mode"] == "live" for u in urls)

    @patch("src.vacancy_search.discovery.crawler_client.fetch_raw_page")
    def test_respects_limit(self, mock_fetch_raw_page, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_fetch_raw_page.return_value = {
            "url": "https://www.careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/",
            "title": "Careers24 Search Results",
            "text_content": CAREERS24_LISTING_FIXTURE,
            "_source_mode": "live",
        }

        urls = discover_job_urls("careers24", limit=1)

        assert len(urls) == 1

    @patch("src.vacancy_search.discovery.crawler_client.fetch_raw_page")
    def test_offline_mode_returns_fixture_without_any_fetch_call(
        self, mock_fetch_raw_page, monkeypatch
    ):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        urls = discover_job_urls("careers24", limit=25)

        mock_fetch_raw_page.assert_not_called()
        assert len(urls) >= 1
        assert all(u["_source_mode"] == "fixture" for u in urls)
        assert all(u["url"] for u in urls)
