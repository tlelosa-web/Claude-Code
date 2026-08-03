from unittest.mock import patch, MagicMock

import pytest
import requests

from src.research import ollama_client
from src.research.ollama_client import (
    call_ollama,
    OllamaError,
    OllamaUnreachableError,
)


def _mock_response(status_code=200, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text
    return resp


class TestCallOllamaHappyPath:
    @patch("src.research.ollama_client.requests.post")
    def test_success_parses_response_field(self, mock_post, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        mock_post.return_value = _mock_response(
            json_data={"response": "This company needs automation."}
        )

        result = call_ollama("Summarise this company.")

        assert result == "This company needs automation."
        mock_post.assert_called_once()

    @patch("src.research.ollama_client.requests.post")
    def test_calls_native_generate_endpoint_with_expected_payload(
        self, mock_post, monkeypatch
    ):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
        mock_post.return_value = _mock_response(json_data={"response": "ok"})

        call_ollama("test prompt")

        call_args = mock_post.call_args
        assert call_args.args[0] == "http://localhost:11434/api/generate"
        payload = call_args.kwargs["json"]
        assert payload["model"] == "qwen3:8b"
        assert payload["prompt"] == "test prompt"
        assert payload["stream"] is False

    @patch("src.research.ollama_client.requests.post")
    def test_requests_clean_prose_via_think_false(self, mock_post, monkeypatch):
        mock_post.return_value = _mock_response(json_data={"response": "ok"})

        call_ollama("test prompt")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["think"] is False

    @patch("src.research.ollama_client.requests.post")
    def test_strips_think_block_from_response(self, mock_post, monkeypatch):
        mock_post.return_value = _mock_response(
            json_data={
                "response": "<think>reasoning about the company</think>Clean summary text."
            }
        )

        result = call_ollama("test prompt")

        assert "reasoning" not in result
        assert result.strip() == "Clean summary text."

    def test_read_timeout_is_120s(self):
        assert ollama_client.READ_TIMEOUT == 120

    @patch("src.research.ollama_client.requests.post")
    def test_request_uses_120s_read_timeout(self, mock_post, monkeypatch):
        mock_post.return_value = _mock_response(json_data={"response": "ok"})

        call_ollama("test prompt")

        call_args = mock_post.call_args
        assert call_args.kwargs["timeout"] == (
            ollama_client.CONNECT_TIMEOUT,
            120,
        )

    @patch("src.research.ollama_client.requests.post")
    def test_payload_includes_keep_alive_30m(self, mock_post, monkeypatch):
        mock_post.return_value = _mock_response(json_data={"response": "ok"})

        call_ollama("test prompt")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["keep_alive"] == "30m"

    @patch("src.research.ollama_client.requests.post")
    def test_no_api_key_required(self, mock_post, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        mock_post.return_value = _mock_response(json_data={"response": "ok"})

        result = call_ollama("test prompt")

        assert result == "ok"
        headers = mock_post.call_args.kwargs.get("headers")
        if headers:
            assert "Authorization" not in headers


class TestCallOllamaRateLimiting:
    @patch("src.research.ollama_client.requests.post")
    def test_rate_limiter_acquire_called_before_request(self, mock_post, monkeypatch):
        mock_post.return_value = _mock_response(json_data={"response": "ok"})
        mock_acquire = MagicMock()
        monkeypatch.setattr("src.research.ollama_client._limiter.acquire", mock_acquire)

        call_ollama("test prompt")

        mock_acquire.assert_called_once()


class TestCallOllamaUnreachable:
    @patch("src.research.ollama_client.requests.post")
    def test_connection_refused_raises_unreachable(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        with pytest.raises(OllamaUnreachableError, match="not reachable"):
            call_ollama("test prompt")

    @patch("src.research.ollama_client.requests.post")
    def test_connect_timeout_raises_unreachable(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectTimeout("timed out")

        with pytest.raises(OllamaUnreachableError, match="not reachable"):
            call_ollama("test prompt")


class TestCallOllamaReadTimeout:
    """A read timeout means the daemon answered the connection and is
    generating — just slowly (cold-loading qwen3:8b, large prompt). This
    must NOT be conflated with the connection-refused/connect-timeout
    "daemon isn't running" case (see ADR-004)."""

    @patch("src.research.ollama_client.requests.post")
    def test_read_timeout_does_not_raise_unreachable(self, mock_post):
        mock_post.side_effect = requests.exceptions.ReadTimeout("timed out")

        with pytest.raises(OllamaError) as exc_info:
            call_ollama("test prompt")

        assert not isinstance(exc_info.value, OllamaUnreachableError)

    @patch("src.research.ollama_client.requests.post")
    def test_read_timeout_message_does_not_claim_daemon_not_running(self, mock_post):
        mock_post.side_effect = requests.exceptions.ReadTimeout("timed out")

        with pytest.raises(OllamaError) as exc_info:
            call_ollama("test prompt")

        assert "is it running" not in str(exc_info.value)

    @patch("src.research.ollama_client.requests.post")
    def test_read_timeout_message_explains_slow_or_cold_loading(self, mock_post):
        mock_post.side_effect = requests.exceptions.ReadTimeout("timed out")

        with pytest.raises(OllamaError, match="timed out generating"):
            call_ollama("test prompt")

        with pytest.raises(OllamaError, match="cold-loading"):
            call_ollama("test prompt")


class TestCallOllamaErrors:
    @patch("src.research.ollama_client.requests.post")
    def test_non_200_raises_ollama_error(self, mock_post):
        mock_post.return_value = _mock_response(status_code=500, text="internal error")

        with pytest.raises(OllamaError, match="500"):
            call_ollama("test prompt")

    @patch("src.research.ollama_client.requests.post")
    def test_bad_response_shape_raises_ollama_error(self, mock_post):
        mock_post.return_value = _mock_response(json_data={"unexpected": "shape"})

        with pytest.raises(OllamaError):
            call_ollama("test prompt")

    @patch("src.research.ollama_client.requests.post")
    def test_generic_request_exception_raises_ollama_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("boom")

        with pytest.raises(OllamaError):
            call_ollama("test prompt")
