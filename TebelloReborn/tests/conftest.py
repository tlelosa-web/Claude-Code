import importlib
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def mock_log_session(monkeypatch):
    """Prevent CLI test runs from appending noise to the real docs/session-log.md.

    Mirrors ai-outreach-agency/tests/conftest.py, but src/main.py doesn't
    exist yet this early in the build (it lands in Phase 7) — a bare
    `monkeypatch.setattr("src.main._log_session", ..., raising=False)` still
    raises ModuleNotFoundError because `raising=False` only covers a missing
    *attribute* on an existing module, not a missing module. Guard the import
    so this stays a true no-op until src/main.py exists.
    """
    try:
        importlib.import_module("src.main")
    except ModuleNotFoundError:
        return
    monkeypatch.setattr("src.main._log_session", MagicMock(), raising=False)
