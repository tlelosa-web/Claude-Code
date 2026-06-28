import os
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "true")


@pytest.fixture(autouse=True)
def mock_update_lead_status(monkeypatch):
    noop = MagicMock()
    monkeypatch.setattr("src.lead_import.db.update_lead_status", noop, raising=False)
    for mod in (
        "src.research.pipeline",
        "src.asset_gen.pipeline",
        "src.approval.cli",
        "src.email_draft.pipeline",
    ):
        monkeypatch.setattr(f"{mod}.update_lead_status", noop, raising=False)
    return noop
