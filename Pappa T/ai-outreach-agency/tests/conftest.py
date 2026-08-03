from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_log_session(monkeypatch):
    """Prevent CLI test runs from appending noise to the real docs/session-log.md."""
    monkeypatch.setattr("src.main._log_session", MagicMock(), raising=False)
