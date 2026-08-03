import os
from unittest.mock import patch, MagicMock

import pytest

from src.shared.openrouter_client import call_openrouter, OpenRouterError


def _mock_response(status_code=200, json_data=None, text="", headers=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    resp.headers = headers or {}
    return resp


class TestCallOpenRouter:
    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with pytest.raises(OpenRouterError, match="OPENROUTER_API_KEY is not set"):
            call_openrouter("test prompt")

    @patch("src.shared.openrouter_client.requests.post")
    def test_happy_path(self, mock_post, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")
        mock_post.return_value = _mock_response(
            json_data={
                "choices": [{"message": {"content": "Generated summary text."}}]
            }
        )

        result = call_openrouter("Summarise this company.")

        assert result == "Generated summary text."
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "Bearer sk-test-key" in call_kwargs.kwargs["headers"]["Authorization"]

    @patch("src.shared.openrouter_client.requests.post")
    @patch("src.shared.openrouter_client.time.sleep")
    def test_429_retries_then_succeeds(self, mock_sleep, mock_post, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")

        rate_limit_resp = _mock_response(
            status_code=429, headers={"Retry-After": "2"}
        )
        success_resp = _mock_response(
            json_data={
                "choices": [{"message": {"content": "Retry succeeded."}}]
            }
        )
        mock_post.side_effect = [rate_limit_resp, success_resp]

        result = call_openrouter("test prompt")

        assert result == "Retry succeeded."
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(2)

    @patch("src.shared.openrouter_client.requests.post")
    def test_500_raises_error(self, mock_post, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")
        mock_post.return_value = _mock_response(
            status_code=500, text="Internal server error"
        )

        with pytest.raises(OpenRouterError, match="API error 500"):
            call_openrouter("test prompt")

    @patch("src.shared.openrouter_client.requests.post")
    def test_malformed_response_raises(self, mock_post, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-key")
        mock_post.return_value = _mock_response(json_data={"choices": []})

        with pytest.raises(OpenRouterError, match="Unexpected response structure"):
            call_openrouter("test prompt")


class TestOfflineMode:
    def test_summariser_offline(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")
        from src.lead_import.schema import Lead
        from src.research.claude_summariser import summarise_lead

        lead = Lead(
            id=1,
            company_name="Test Co",
            contact_name="J",
            contact_title="Mgr",
            email="j@test.co.za",
            source="manual",
        )
        result = summarise_lead(lead, {"title": "Test Co", "about": "a firm"})
        assert "Test Co" in result

    def test_generator_offline(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")
        from src.lead_import.schema import Lead
        from src.research.schema import ResearchResult
        from src.asset_gen.generator import generate_asset

        lead = Lead(
            id=1,
            company_name="Test Co",
            contact_name="J",
            contact_title="Mgr",
            email="j@test.co.za",
            source="manual",
        )
        research = ResearchResult(lead_id=1, summary="A summary.", raw_data={})
        result = generate_asset(lead, research)
        assert "Test Co" in result.asset_text
