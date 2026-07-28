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
