"""RED: src/submission/eligibility.py doesn't exist yet — these imports must
fail first.

Dispatch is capability-based, not platform-only: an adapter is looked up by
platform and then asked `can_handle(vacancy)` (docs/specs/submission-core.md
Amendment A3). Indeed's flow varies per employer — many postings redirect to an
external ATS — so a registered adapter must be able to decline an individual
vacancy and have it fall through to manual, not be assumed capable because its
platform matched.

The registry ships empty in this build. That is the design, not an omission:
with no adapter, every vacancy routes to manual, visibly and on the record.
"""

import pytest

from src.submission.eligibility import ADAPTERS, get_adapter, is_auto_submittable
from src.vacancy_search.schema import Vacancy


class _FakeAdapter:
    """Stands in for a real site adapter. Deliberately not registered by
    default — tests inject it, so the shipped registry stays empty."""

    def __init__(self, platform: str, handles: bool = True):
        self.platform = platform
        self._handles = handles

    def can_handle(self, vacancy: Vacancy) -> bool:
        return self._handles

    def submit(self, vacancy: Vacancy, session_state_path) -> tuple[bool, str]:
        return True, "submitted by fake adapter"


@pytest.fixture
def registry(monkeypatch):
    """Isolate the module-level registry so no test leaks an adapter into
    another — the shipped registry being empty is an assertion elsewhere."""
    fake_registry: dict = {}
    monkeypatch.setattr("src.submission.eligibility.ADAPTERS", fake_registry)
    return fake_registry


def _vacancy(platform="indeed"):
    return Vacancy(
        company="Acme",
        title="Operations Foreman",
        url="https://example.com/job/1",
        platform=platform,
        status="approved",
    )


class TestShippedRegistry:
    def test_registry_is_empty_in_this_build(self):
        """The core ships with no adapters. If this fails, an adapter was added
        without the platform decision in the spec's Open Items being answered."""
        assert ADAPTERS == {}

    @pytest.mark.parametrize("platform", ["indeed", "linkedin", "pnet", "careers24"])
    def test_nothing_is_auto_submittable(self, platform):
        assert is_auto_submittable(_vacancy(platform)) is False

    def test_get_adapter_returns_none(self):
        assert get_adapter(_vacancy()) is None


class TestCapabilityDispatch:
    def test_registered_adapter_that_handles_is_auto_submittable(self, registry):
        registry["indeed"] = _FakeAdapter("indeed", handles=True)

        assert is_auto_submittable(_vacancy("indeed")) is True

    def test_registered_adapter_can_decline_an_individual_vacancy(self, registry):
        """Platform matched, adapter said no — e.g. an external-ATS redirect.
        Must fall through to manual rather than be attempted."""
        registry["indeed"] = _FakeAdapter("indeed", handles=False)

        assert is_auto_submittable(_vacancy("indeed")) is False

    def test_other_platforms_unaffected_by_one_registration(self, registry):
        registry["indeed"] = _FakeAdapter("indeed", handles=True)

        assert is_auto_submittable(_vacancy("pnet")) is False

    def test_get_adapter_returns_the_registered_adapter(self, registry):
        adapter = _FakeAdapter("indeed", handles=True)
        registry["indeed"] = adapter

        assert get_adapter(_vacancy("indeed")) is adapter

    def test_get_adapter_returns_none_when_adapter_declines(self, registry):
        """get_adapter is what the pipeline dispatches on, so a declining
        adapter must be indistinguishable from no adapter at all."""
        registry["indeed"] = _FakeAdapter("indeed", handles=False)

        assert get_adapter(_vacancy("indeed")) is None
