from unittest.mock import patch, MagicMock

import pytest
import requests as _requests

from src.research.apify_client import ApifyClient, FALLBACK


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else []
    resp.raise_for_status.side_effect = (
        None if status_code < 400
        else _requests.HTTPError(response=resp)
    )
    return resp


class TestApifyClient:
    @patch("src.research.apify_client.requests.post")
    def test_happy_path(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        mock_post.return_value = _mock_response(
            json_data=[
                {
                    "title": "Acme Engineering",
                    "description": "Steel fabrication firm.",
                    "text": "Acme provides plant maintenance and steel work.",
                }
            ]
        )

        client = ApifyClient()
        result = client.scrape_company("https://acme.co.za")

        assert result["title"] == "Acme Engineering"
        assert result["description"] == "Steel fabrication firm."
        assert "plant maintenance" in result["text_content"]
        assert result["url"] == "https://acme.co.za"
        mock_post.assert_called_once()

    @patch("src.research.apify_client.requests.post")
    def test_empty_response_returns_fallback(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        mock_post.return_value = _mock_response(json_data=[])

        client = ApifyClient()
        result = client.scrape_company("https://empty.co.za")

        assert result["text_content"] == "No data found"
        assert result["title"] == ""
        assert result["url"] == "https://empty.co.za"

    @patch("src.research.apify_client.requests.post")
    def test_text_truncated_to_2000_chars(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        long_text = "x" * 5000
        mock_post.return_value = _mock_response(
            json_data=[{"title": "T", "text": long_text}]
        )

        client = ApifyClient()
        result = client.scrape_company("https://long.co.za")

        assert len(result["text_content"]) == 2000

    @patch("src.research.apify_client.requests.post")
    def test_http_error_returns_fallback(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        mock_post.return_value = _mock_response(status_code=500)

        client = ApifyClient()
        result = client.scrape_company("https://broken.co.za")

        assert result["text_content"] == "No data found"

    def test_missing_api_key_returns_fallback(self, monkeypatch):
        monkeypatch.delenv("APIFY_API_KEY", raising=False)
        monkeypatch.delenv("OFFLINE_MODE", raising=False)

        client = ApifyClient()
        result = client.scrape_company("https://nokey.co.za")

        assert result["text_content"] == "No data found"

    def test_offline_mode_returns_fixture(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        client = ApifyClient()
        result = client.scrape_company("https://offline.co.za")

        assert result["title"] == "Example Engineering Co."
        assert result["url"] == "https://offline.co.za"
        assert "services" in result
