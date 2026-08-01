"""RED: src/vacancy_search/discovery.py doesn't exist yet — these imports
must fail first.

Amendment — Automated Discovery Redesign (2026-07-29): discovery.py builds
platform search URLs, parses individual job-detail-page URLs out of a
listing page's raw text (a deterministic parse, never an LLM call — judgment
call #1), and gates PNet behind a manual-verification config, falling back
to the pre-existing data/crawler_seed_urls.json for PNet only.
"""

import json
from unittest.mock import patch

from src.vacancy_search.discovery import (
    build_search_url,
    discover_job_urls,
    get_job_urls,
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

# Readability-extracted text has zero hrefs — confirmed against a real page
# (2026-08-01, no hrefs of any kind survive the actor's default
# htmlTransformer). Used to prove discover_job_urls() parses "html", not
# "text_content" (the bug this regression test locks down).
NO_URLS_TEXT_CONTENT = "Operations Foreman Jobs in Gauteng. 25 results found."

# Real anchor shape confirmed via direct real-API test against
# https://www.pnet.co.za/jobs/operations-foreman/in-gauteng with
# htmlTransformer: "none" (2026-08-01) — job-detail links are
# domain-relative, shaped /jobs--<slug>--<numeric-id>-inline.html, inside an
# <a data-testid="job-item-title"> anchor. Trimmed/synthesized from the real
# structure, not a verbatim scrape.
PNET_LISTING_FIXTURE = """
<html><body>
<h2><a href="/jobs--Panelshop-Foreman-Johannesburg-Scania-S-A-Pty-Ltd--4243343-inline.html" data-testid="job-item-title">Panelshop Foreman</a></h2>
<h2><a href="/jobs--Foreman-Supervisor-Fochville-SET--4240854-inline.html" data-testid="job-item-title">Foreman / Supervisor</a></h2>
<a href="/jobs/general-manager/in-gauteng">General Manager Jobs</a>
<a href="/jobs/operations-foreman/in-gauteng?action=facet_selected;worktypes;80001">Full-time</a>
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


class TestBuildSearchUrlPnet:
    """PNet's live robots.txt (User-agent: *) includes
    "Disallow: /jobs/*?*" — the query-string shape
    (?radius=30&searchOrigin=...) the site itself redirects a browser search
    onto is explicitly disallowed for generic crawlers, confirmed live
    2026-07-29. build_search_url("pnet", ...) must return ONLY the bare
    path-only shape (no "?"), under every input — this is asserted
    structurally below, not just by convention."""

    def test_returns_bare_path_only_shape(self):
        url = build_search_url("pnet", "Operations Foreman", "Gauteng")

        assert url == "https://www.pnet.co.za/jobs/operations-foreman/in-gauteng"

    def test_never_contains_a_query_string_character(self):
        for title, location in [
            ("Operations Foreman", "Gauteng"),
            ("Project Engineer (Mechanical)?", "Gauteng, South Africa"),
            ("weird & title", "Cape Town"),
        ]:
            url = build_search_url("pnet", title, location)

            assert "?" not in url


class TestPnetSlugSlashHandling:
    """Bonus finding #3 in docs/bugs/pnet-careers24-discovery-zero-results.md:
    _pnet_slug used to silently drop "/" instead of treating it as a
    separator, concatenating "Operations Foreman/Manager" into
    "operations-foremanmanager". Fixed: "/" is now a separator, same as
    whitespace."""

    def test_slash_becomes_a_separator_not_dropped(self):
        url = build_search_url("pnet", "Operations Foreman/Manager", "Gauteng")

        assert "foremanmanager" not in url
        assert "foreman-manager" in url

    def test_still_never_contains_a_query_string_character(self):
        url = build_search_url("pnet", "Operations Foreman/Manager", "Gauteng")

        assert "?" not in url


class TestParseJobUrlsFromListingPnet:
    """Real anchor shape confirmed 2026-08-01 (see PNET_LISTING_FIXTURE):
    domain-relative hrefs, /jobs--<slug>--<numeric-id>-inline.html, must be
    resolved to absolute URLs (crawler_client.fetch_raw_page needs a full
    URL for the follow-up job-detail fetch)."""

    def test_extracts_and_resolves_job_detail_urls(self):
        urls = parse_job_urls_from_listing(PNET_LISTING_FIXTURE, "pnet")

        assert (
            "https://www.pnet.co.za/jobs--Panelshop-Foreman-Johannesburg-Scania-S-A-Pty-Ltd--4243343-inline.html"
            in urls
        )
        assert (
            "https://www.pnet.co.za/jobs--Foreman-Supervisor-Fochville-SET--4240854-inline.html"
            in urls
        )

    def test_does_not_include_related_search_or_facet_links(self):
        """The listing page also contains /jobs/<category>/in-<location>
        "related search" links (confirmed real, 2026-08-01) — a completely
        different path shape from job-detail links and must not be picked
        up as if they were postings."""
        urls = parse_job_urls_from_listing(PNET_LISTING_FIXTURE, "pnet")

        assert not any("/jobs/general-manager" in u for u in urls)
        assert not any("action=facet_selected" in u for u in urls)


class TestDiscoverJobUrlsPnet:
    @patch("src.vacancy_search.discovery.crawler_client.fetch_raw_page")
    def test_fetches_listing_then_parses_and_resolves_job_urls(
        self, mock_fetch_raw_page, monkeypatch
    ):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_fetch_raw_page.return_value = {
            "url": "https://www.pnet.co.za/jobs/operations-foreman/in-gauteng",
            "title": "PNet Search Results",
            "text_content": NO_URLS_TEXT_CONTENT,
            "html": PNET_LISTING_FIXTURE,
            "_source_mode": "live",
        }

        urls = discover_job_urls("pnet", limit=25)

        assert len(urls) == 2
        assert all(u["url"].startswith("https://www.pnet.co.za/") for u in urls)
        assert all(u["_source_mode"] == "live" for u in urls)


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
            "text_content": NO_URLS_TEXT_CONTENT,
            "html": CAREERS24_LISTING_FIXTURE,
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
            "text_content": NO_URLS_TEXT_CONTENT,
            "html": CAREERS24_LISTING_FIXTURE,
            "_source_mode": "live",
        }

        urls = discover_job_urls("careers24", limit=1)

        assert len(urls) == 1

    @patch("src.vacancy_search.discovery.crawler_client.fetch_raw_page")
    def test_parses_html_field_not_text_content(self, mock_fetch_raw_page, monkeypatch):
        """Regression lock for the real root cause (2026-08-01): a listing
        page whose text_content has zero URLs (matching real readability
        output) must still yield job URLs, because discovery reads "html",
        not "text_content"."""
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_fetch_raw_page.return_value = {
            "url": "https://www.careers24.com/jobs/lc-gauteng/kw-operations-foreman/rmt-incl/",
            "title": "Careers24 Search Results",
            "text_content": NO_URLS_TEXT_CONTENT,
            "html": CAREERS24_LISTING_FIXTURE,
            "_source_mode": "live",
        }

        urls = discover_job_urls("careers24", limit=25)

        assert len(urls) == 2

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


class TestGetJobUrls:
    """get_job_urls(platform, limit) — the single entry point
    apify_client.py::fetch_vacancies() calls for both platforms. Careers24
    has no gate (always discover_job_urls). PNet branches on
    data/discovery_config.json's mode: "manual_pending_verification" falls
    back to the pre-existing data/crawler_seed_urls.json unchanged, "auto"
    calls discover_job_urls("pnet", limit) instead — one function, branching
    on config, no `if platform == "pnet"` special-casing in any consumer."""

    @patch("src.vacancy_search.discovery.discover_job_urls")
    def test_careers24_always_calls_discover_job_urls(self, mock_discover, tmp_path):
        mock_discover.return_value = [
            {"url": "https://example.co.za/careers24-1", "_source_mode": "live"}
        ]
        config_path = tmp_path / "discovery_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "pnet": {"mode": "manual_pending_verification"},
                    "careers24": {"mode": "manual_pending_verification"},
                }
            )
        )

        urls = get_job_urls(
            "careers24", limit=25, discovery_config_path=str(config_path)
        )

        mock_discover.assert_called_once_with("careers24", 25)
        assert urls == ["https://example.co.za/careers24-1"]

    @patch("src.vacancy_search.discovery.discover_job_urls")
    @patch("src.vacancy_search.discovery.build_search_url")
    def test_pnet_manual_pending_verification_falls_back_to_seed_urls(
        self, mock_build_search_url, mock_discover, tmp_path
    ):
        config_path = tmp_path / "discovery_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "pnet": {"mode": "manual_pending_verification"},
                    "careers24": {"mode": "auto"},
                }
            )
        )
        seed_path = tmp_path / "crawler_seed_urls.json"
        seed_path.write_text(
            json.dumps({"pnet": ["https://example.co.za/pnet-seed-1"]})
        )

        urls = get_job_urls(
            "pnet",
            limit=25,
            discovery_config_path=str(config_path),
            seed_urls_path=str(seed_path),
        )

        mock_discover.assert_not_called()
        mock_build_search_url.assert_not_called()
        assert urls == ["https://example.co.za/pnet-seed-1"]

    @patch("src.vacancy_search.discovery.discover_job_urls")
    def test_pnet_auto_mode_calls_discover_job_urls(self, mock_discover, tmp_path):
        mock_discover.return_value = [
            {"url": "https://example.co.za/pnet-discovered-1", "_source_mode": "live"}
        ]
        config_path = tmp_path / "discovery_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "pnet": {"mode": "auto"},
                    "careers24": {"mode": "auto"},
                }
            )
        )

        urls = get_job_urls("pnet", limit=25, discovery_config_path=str(config_path))

        mock_discover.assert_called_once_with("pnet", 25)
        assert urls == ["https://example.co.za/pnet-discovered-1"]
