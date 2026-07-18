from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_log_session(monkeypatch):
    """Prevent CLI test runs from appending noise to the real docs/session-log.md.

    `raising=False` so this stays a no-op until src/main.py (and its
    `_log_session` helper) exist — mirrors ai-outreach-agency/tests/conftest.py.
    """
    monkeypatch.setattr("src.main._log_session", MagicMock(), raising=False)
