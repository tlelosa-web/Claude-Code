import os

import pytest


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "true")
