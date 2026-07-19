from unittest.mock import patch

import pytest

from src.lead_import.schema import Lead
from src.research.claude_summariser import summarise_lead
from src.research.ollama_client import OllamaUnreachableError


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        id=1,
        company_name="Test Co",
        contact_name="J",
        contact_title="Mgr",
        email="j@test.co.za",
        source="manual",
    )
    defaults.update(overrides)
    return Lead(**defaults)


class TestOfflineModePreserved:
    def test_offline_mode_returns_stub_summary(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        lead = _make_lead()
        result = summarise_lead(lead, {"title": "Test Co", "about": "a firm"})

        assert "Test Co" in result

    @patch("src.research.claude_summariser.call_ollama")
    def test_offline_mode_never_calls_ollama(self, mock_call_ollama, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        lead = _make_lead()
        summarise_lead(lead, {"title": "Test Co", "about": "a firm"})

        mock_call_ollama.assert_not_called()


class TestNonOfflineCallsOllama:
    @patch("src.research.claude_summariser.call_ollama")
    def test_non_offline_calls_call_ollama(self, mock_call_ollama, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.return_value = "A local model summary."

        lead = _make_lead()
        result = summarise_lead(lead, {"title": "Test Co", "about": "a firm"})

        assert result == "A local model summary."
        mock_call_ollama.assert_called_once()

    def test_call_openrouter_not_imported(self):
        import src.research.claude_summariser as mod

        assert not hasattr(mod, "call_openrouter")

    @patch("src.research.claude_summariser.call_ollama")
    def test_unreachable_ollama_propagates_no_openrouter_fallback(
        self, mock_call_ollama, monkeypatch
    ):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_call_ollama.side_effect = OllamaUnreachableError(
            "Ollama not reachable at http://localhost:11434 — is it running?"
        )

        lead = _make_lead()
        with pytest.raises(OllamaUnreachableError, match="not reachable"):
            summarise_lead(lead, {"title": "Test Co", "about": "a firm"})
