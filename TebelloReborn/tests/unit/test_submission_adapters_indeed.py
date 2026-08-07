"""RED: src/submission/adapters/ doesn't exist yet — these imports must fail
first.

Phase E of docs/specs/indeed-submit-adapter.md: A1's static `can_handle()`
predicate, and the observation dataclasses (`ExtractedQuestion`, `PrepResult`)
that `inspect_apply_flow()` returns.

**A1 is the finding with the widest blast radius, and its tests are about what
`can_handle()` must NOT do.** `eligibility.get_adapter()` calls it on every
`submit` run — including `--manual` and every `not_supported` case — so a
predicate that opens a browser puts a network action inside what the core treats
as a dict lookup. Purity here is a contract, not a style preference.

The six URLs below are the real ones: `career.db`'s six approved Indeed
vacancies, read out of the live database rather than invented, so the predicate
is tested against the shape it will actually meet.
"""

import pytest

from src.submission.adapters.indeed import IndeedAdapter
from src.submission.schema import (
    ExtractedQuestion,
    FieldType,
    PrepResult,
    PrepStatus,
)
from src.vacancy_search.schema import Vacancy

# Verbatim from career.db, status='approved', 2026-08-08.
LIVE_APPROVED_URLS = [
    "https://za.indeed.com/viewjob?jk=08c7721d53f3cbc5",
    "https://za.indeed.com/viewjob?jk=d7d04674eabafbac",
    "https://za.indeed.com/viewjob?jk=03b38b6acadbede4",
    "https://za.indeed.com/viewjob?jk=de6a49edd1c42d18",
    "https://za.indeed.com/viewjob?jk=529d2a7553c76f4f",
    "https://za.indeed.com/viewjob?jk=7b300b2687ec1209",
]


def vacancy_at(url: str, platform: str = "indeed") -> Vacancy:
    return Vacancy(
        id=1, company="Utopia", title="Project Engineer", url=url, platform=platform
    )


@pytest.fixture
def adapter():
    return IndeedAdapter()


class TestCanHandleAccepts:
    def test_every_live_approved_vacancy(self, adapter):
        # If this ever goes red, the six applications this whole spec exists to
        # unblock silently route to manual again.
        for url in LIVE_APPROVED_URLS:
            assert adapter.can_handle(vacancy_at(url)), url

    def test_the_bare_apex_domain(self, adapter):
        assert adapter.can_handle(vacancy_at("https://indeed.com/viewjob?jk=abc"))

    @pytest.mark.parametrize("host", ["za.indeed.com", "www.indeed.com", "indeed.com"])
    def test_any_country_subdomain(self, adapter, host):
        assert adapter.can_handle(vacancy_at(f"https://{host}/viewjob?jk=abc"))

    def test_ignores_query_and_fragment(self, adapter):
        assert adapter.can_handle(
            vacancy_at("https://za.indeed.com/viewjob?jk=abc&from=serp#top")
        )


class TestCanHandleDeclines:
    def test_a_different_platform(self, adapter):
        assert not adapter.can_handle(
            vacancy_at("https://za.indeed.com/viewjob?jk=abc", platform="linkedin")
        )

    def test_a_non_viewjob_path(self, adapter):
        assert not adapter.can_handle(vacancy_at("https://za.indeed.com/jobs?q=engineer"))

    def test_a_lookalike_suffix_domain(self, adapter):
        # "notindeed.com".endswith("indeed.com") is True. A1's sketch is written
        # that way, and browser.py's _is_google_block_page already avoids the
        # same trap deliberately — matching it here is the point of the test.
        assert not adapter.can_handle(
            vacancy_at("https://notindeed.com/viewjob?jk=abc")
        )

    def test_a_domain_that_merely_contains_indeed(self, adapter):
        assert not adapter.can_handle(
            vacancy_at("https://indeed.com.evil.example/viewjob?jk=abc")
        )

    def test_a_malformed_url(self, adapter):
        assert not adapter.can_handle(vacancy_at("not a url at all"))

    def test_an_empty_url(self, adapter):
        assert not adapter.can_handle(vacancy_at(""))


class TestCanHandleIsPure:
    """A1: pure, offline, side-effect-free. Called on every submit run."""

    def test_does_not_touch_the_network(self, adapter, monkeypatch):
        def explode(*args, **kwargs):
            raise AssertionError("can_handle() opened a browser")

        # If the predicate ever grows a live check, it has to go through one of
        # these — and each is the exact regression A1 exists to prevent.
        monkeypatch.setattr(
            "src.submission.browser.authenticated_page", explode, raising=False
        )
        monkeypatch.setattr(
            "src.submission.browser.require_session_state", explode, raising=False
        )

        for url in LIVE_APPROVED_URLS:
            adapter.can_handle(vacancy_at(url))

    def test_is_stable_across_repeated_calls(self, adapter):
        vacancy = vacancy_at(LIVE_APPROVED_URLS[0])
        assert [adapter.can_handle(vacancy) for _ in range(3)] == [True, True, True]


class TestAdapterContract:
    def test_declares_its_platform(self, adapter):
        assert adapter.platform == "indeed"

    def test_submit_reports_failure_rather_than_raising(self, adapter, tmp_path):
        # Phase G builds the real one. Until then submit() must not raise: an
        # exception reaches pipeline.py as "adapter raised: ..." which reads like
        # a bug, where the truth is simply that this half isn't built yet.
        succeeded, detail = adapter.submit(
            vacancy_at(LIVE_APPROVED_URLS[0]), tmp_path / "state.json"
        )
        assert succeeded is False
        assert "phase g" in detail.lower()

    def test_is_not_registered_yet(self):
        # inspect_apply_flow() needs selectors that only live recon can supply.
        # Registering before then would let a vacancy reach a prep run that can
        # only fail — the same empty-until-known discipline WIZARD_STEPS and
        # ADAPTERS already follow.
        from src.submission.eligibility import ADAPTERS

        assert "indeed" not in ADAPTERS


class TestExtractedQuestion:
    """What the adapter observed — no judgment, no fingerprint, no draft."""

    def test_carries_only_observations(self):
        question = ExtractedQuestion(
            question_text="Location",
            field_type=FieldType.TEXT,
            step_url="https://smartapply.indeed.com/x",
            position=0,
        )
        # Sensitivity and fingerprint are questions.py's job, and drafted_answer
        # is drafting.py's. An adapter that could set them would be judging what
        # it observed, which is the split Phase D established.
        for judged in ("sensitivity", "fingerprint", "drafted_answer", "decision"):
            assert not hasattr(question, judged), judged

    def test_rejects_a_raw_field_type(self):
        with pytest.raises(TypeError):
            ExtractedQuestion(
                question_text="Location",
                field_type="text",
                step_url="https://smartapply.indeed.com/x",
                position=0,
            )


class TestPrepResult:
    def test_questions_extracted_requires_at_least_one_question(self):
        # db.submission_prep_ready() already defends against this state reaching
        # the gate ("recorded questions_extracted but stored no questions").
        # Refusing to construct it stops the bad row being written at all.
        with pytest.raises(ValueError):
            PrepResult(status=PrepStatus.QUESTIONS_EXTRACTED, detail="none found")

    def test_no_questions_refuses_to_carry_questions(self):
        question = ExtractedQuestion(
            question_text="Location",
            field_type=FieldType.TEXT,
            step_url="https://smartapply.indeed.com/x",
            position=0,
        )
        with pytest.raises(ValueError):
            PrepResult(
                status=PrepStatus.NO_QUESTIONS, detail="", questions=(question,)
            )

    def test_a_failure_status_carries_no_questions(self):
        result = PrepResult(
            status=PrepStatus.CAPTCHA_DETECTED,
            detail="captcha challenge detected",
            step_url="https://smartapply.indeed.com/x",
        )
        assert result.questions == ()

    def test_rejects_a_raw_status(self):
        with pytest.raises(TypeError):
            PrepResult(status="no_questions", detail="")
