import pytest


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    """Force OFFLINE_MODE for the whole unit suite — no unit test may touch
    the network. Module-specific mocks (e.g. DB write no-ops) get added here
    per-module as later phases need them, mirroring
    ai-outreach-agency/tests/unit/conftest.py.
    """
    monkeypatch.setenv("OFFLINE_MODE", "true")
