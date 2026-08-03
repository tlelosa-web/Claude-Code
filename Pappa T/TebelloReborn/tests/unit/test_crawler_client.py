"""RED: src/vacancy_search/crawler_client.py doesn't exist yet — these
imports must fail first.

Mirrors ai-outreach-agency/src/research/apify_client.py's FIXTURE convention
and src/vacancy_search/apify_client.py's OFFLINE_MODE / rate-limiter /
graceful-degradation conventions. Never hardcodes literal PNet/Careers24
URLs — seed URLs come only from data/crawler_seed_urls.json.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.vacancy_search.crawler_client import (
    CRAWLER_ACTOR_URL,
    fetch_raw_page,
    fetch_raw_pages,
)

SEED_URLS_PATH = "data/crawler_seed_urls.json"


def _mock_response(json_data):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status.side_effect = None
    return resp


class TestOfflineMode:
    def test_offline_mode_returns_fixture_raw_pages(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        results = fetch_raw_pages("pnet", limit=25, seed_urls_path=SEED_URLS_PATH)

        assert 2 <= len(results) <= 3
        for page in results:
            assert {"url", "title", "text_content"} <= page.keys()

    def test_offline_mode_tags_source_mode_fixture(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        results = fetch_raw_pages("careers24", limit=25, seed_urls_path=SEED_URLS_PATH)

        assert all(page["_source_mode"] == "fixture" for page in results)

    def test_offline_mode_respects_limit(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        results = fetch_raw_pages("pnet", limit=1, seed_urls_path=SEED_URLS_PATH)

        assert len(results) == 1


class TestMissingApiKey:
    def test_missing_api_key_falls_back_to_fixture_with_warning(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.delenv("APIFY_API_KEY", raising=False)

        with pytest.warns(UserWarning, match="APIFY_API_KEY"):
            results = fetch_raw_pages("pnet", limit=25, seed_urls_path=SEED_URLS_PATH)

        assert len(results) >= 1
        assert all(page["_source_mode"] == "fixture" for page in results)


class TestRealCallPath:
    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_calls_rate_limiter_before_each_real_request(
        self, mock_post, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response(
            [{"url": "https://example.co.za/job1", "title": "t", "text": "body"}]
        )

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(
            json.dumps(
                {
                    "pnet": [
                        "https://example.co.za/pnet-job-1",
                        "https://example.co.za/pnet-job-2",
                    ]
                }
            )
        )

        with patch(
            "src.vacancy_search.crawler_client._limiter.acquire"
        ) as mock_acquire:
            fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        assert mock_acquire.call_count == 2

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_calls_generic_crawler_actor_url(self, mock_post, monkeypatch, tmp_path):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response(
            [{"url": "https://example.co.za/job1", "title": "t", "text": "body"}]
        )

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(json.dumps({"pnet": ["https://example.co.za/pnet-job-1"]}))

        fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        called_url = (
            mock_post.call_args.args[0]
            if mock_post.call_args.args
            else mock_post.call_args.kwargs.get("url")
        )
        assert called_url == CRAWLER_ACTOR_URL
        assert "apify~website-content-crawler" in CRAWLER_ACTOR_URL
        assert "run-sync-get-dataset-items" in CRAWLER_ACTOR_URL

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_requests_raw_html_not_readability_extracted(
        self, mock_post, monkeypatch, tmp_path
    ):
        """Real-run finding (2026-08-01): the actor's default htmlTransformer
        (readableText / Mozilla Readability) strips every <a href> from its
        HTML output — confirmed against a real PNet page (0 hrefs found).
        saveHtml alone is not enough; htmlTransformer must be "none" to get
        real anchors back, which discovery.py's link-harvesting depends on."""
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response(
            [
                {
                    "url": "https://example.co.za/job1",
                    "title": "t",
                    "text": "body",
                    "html": "<html></html>",
                }
            ]
        )

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(json.dumps({"pnet": ["https://example.co.za/pnet-job-1"]}))

        fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        payload = mock_post.call_args.kwargs["json"]
        assert payload["saveHtml"] is True
        assert payload["htmlTransformer"] == "none"

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_live_results_tagged_source_mode_live(
        self, mock_post, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response(
            [
                {
                    "url": "https://example.co.za/pnet-job-1",
                    "title": "Operations Foreman",
                    "text": "Job description body.",
                }
            ]
        )

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(json.dumps({"pnet": ["https://example.co.za/pnet-job-1"]}))

        results = fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        assert len(results) == 1
        assert results[0]["_source_mode"] == "live"
        assert results[0]["url"] == "https://example.co.za/pnet-job-1"

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_request_error_on_one_seed_url_does_not_abort_others(
        self, mock_post, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        import requests as _requests

        mock_post.side_effect = [
            _requests.ConnectionError("crawler unreachable"),
            _mock_response(
                [
                    {
                        "url": "https://example.co.za/pnet-job-2",
                        "title": "Project Engineer",
                        "text": "Body.",
                    }
                ]
            ),
        ]

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(
            json.dumps(
                {
                    "pnet": [
                        "https://example.co.za/pnet-job-1",
                        "https://example.co.za/pnet-job-2",
                    ]
                }
            )
        )

        results = fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        assert len(results) == 1
        assert results[0]["url"] == "https://example.co.za/pnet-job-2"
        assert results[0]["_source_mode"] == "live"

    def test_unknown_platform_returns_empty_list(self, monkeypatch, tmp_path):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(json.dumps({"pnet": ["https://example.co.za/pnet-job-1"]}))

        results = fetch_raw_pages("glassdoor", limit=25, seed_urls_path=str(seed_path))

        assert results == []


class TestFetchRawPage:
    """fetch_raw_page(url) — new single-URL primitive (Amendment, judgment
    call #2): fetch_raw_pages() is refactored (step 64) to call this once
    per seed URL instead of duplicating the POST/timeout/_source_mode/
    exception-handling block. discovery.py (Phase 12b) composes on top of
    this same primitive for listing-page and job-detail-page fetches."""

    def test_offline_mode_returns_single_fixture_page(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        page = fetch_raw_page("https://example.co.za/any-url")

        assert {"url", "title", "text_content", "_source_mode"} <= page.keys()
        assert page["_source_mode"] == "fixture"

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_real_call_returns_live_tagged_page(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response(
            [{"url": "https://example.co.za/job1", "title": "Title", "text": "Body"}]
        )

        page = fetch_raw_page("https://example.co.za/job1")

        assert page["_source_mode"] == "live"
        assert page["url"] == "https://example.co.za/job1"
        assert page["title"] == "Title"
        assert page["text_content"] == "Body"

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_real_call_surfaces_raw_html_field(self, mock_post, monkeypatch):
        """The raw "html" field (real anchors, htmlTransformer: none) is
        surfaced separately from "text_content" (still the clean readability
        text extractor.py's LLM prompt consumes) — discovery.py's
        link-harvesting needs the former, extraction needs the latter."""
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response(
            [
                {
                    "url": "https://example.co.za/job1",
                    "title": "Title",
                    "text": "Body",
                    "html": '<a href="/jobs--Foo--123-inline.html">Foo</a>',
                }
            ]
        )

        page = fetch_raw_page("https://example.co.za/job1")

        assert page["html"] == '<a href="/jobs--Foo--123-inline.html">Foo</a>'
        assert page["text_content"] == "Body"

    @patch("src.vacancy_search.crawler_client.requests.post")
    def test_request_error_returns_none(self, mock_post, monkeypatch):
        import requests as _requests

        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.side_effect = _requests.ConnectionError("crawler unreachable")

        page = fetch_raw_page("https://example.co.za/job1")

        assert page is None


class TestFetchRawPagesRegressionAfterRefactor:
    """Regression lock (step 63): fetch_raw_pages()'s existing outward
    behavior (steps 61/62) must be unchanged once refactored to call
    fetch_raw_page() internally per seed URL."""

    @patch("src.vacancy_search.crawler_client.fetch_raw_page")
    def test_fetch_raw_pages_calls_fetch_raw_page_per_seed_url(
        self, mock_fetch_raw_page, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_fetch_raw_page.side_effect = [
            {
                "url": "https://example.co.za/pnet-job-1",
                "title": "t1",
                "text_content": "body1",
                "_source_mode": "live",
            },
            {
                "url": "https://example.co.za/pnet-job-2",
                "title": "t2",
                "text_content": "body2",
                "_source_mode": "live",
            },
        ]

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(
            json.dumps(
                {
                    "pnet": [
                        "https://example.co.za/pnet-job-1",
                        "https://example.co.za/pnet-job-2",
                    ]
                }
            )
        )

        results = fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        assert mock_fetch_raw_page.call_count == 2
        mock_fetch_raw_page.assert_any_call("https://example.co.za/pnet-job-1")
        mock_fetch_raw_page.assert_any_call("https://example.co.za/pnet-job-2")
        assert [p["url"] for p in results] == [
            "https://example.co.za/pnet-job-1",
            "https://example.co.za/pnet-job-2",
        ]

    @patch("src.vacancy_search.crawler_client.fetch_raw_page")
    def test_fetch_raw_pages_skips_none_results(
        self, mock_fetch_raw_page, monkeypatch, tmp_path
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_fetch_raw_page.side_effect = [
            None,
            {
                "url": "https://example.co.za/pnet-job-2",
                "title": "t2",
                "text_content": "body2",
                "_source_mode": "live",
            },
        ]

        seed_path = tmp_path / "seed_urls.json"
        seed_path.write_text(
            json.dumps(
                {
                    "pnet": [
                        "https://example.co.za/pnet-job-1",
                        "https://example.co.za/pnet-job-2",
                    ]
                }
            )
        )

        results = fetch_raw_pages("pnet", limit=25, seed_urls_path=str(seed_path))

        assert len(results) == 1
        assert results[0]["url"] == "https://example.co.za/pnet-job-2"
