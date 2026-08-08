"""RED: src/submission/prep.py doesn't exist yet — these imports must fail first.

Phase E of docs/specs/indeed-submit-adapter.md: the `prep-submission`
orchestration. Everything the adapter observes gets judged and persisted here,
so this module is where B1 (same status gate as submit), B2 (prep never
transitions status) and B3 (adapters never touch the database) are actually
enforced.

**The adapter is a fake in every test.** That is not a shortcut around the live
recon — it is the same separation Phase D made: the real adapter's only job is
to return a `PrepResult`, so every decision made *about* one is testable now,
and the live half is reduced to producing the object these tests already pin.
"""

import shutil
import sqlite3

import pytest

from src.profile.db import init_db as init_profile_db, upsert_profile
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane
from src.submission.db import (
    get_latest_prep,
    get_questions_for_prep,
    init_db as init_submission_db,
    submission_prep_ready,
)
from src.submission.prep import (
    PrepNotSupportedError,
    SessionSetupRequiredError,
    run_prep,
)
from src.submission.pipeline import SubmissionNotAllowedError
from src.submission.questions import compute_fingerprint
from src.submission.schema import (
    ExtractedQuestion,
    FieldType,
    PrepResult,
    PrepStatus,
    QuestionDecision,
    Sensitivity,
)
from src.vacancy_search.db import get_by_id, init_db as init_vacancy_db, insert_vacancy
from src.vacancy_search.schema import Vacancy

INDEED_URL = "https://za.indeed.com/viewjob?jk=d7d04674eabafbac"
STEP_URL = (
    "https://smartapply.indeed.com/beta/indeedapply/form/questions-module/questions/1"
)


class FakeAdapter:
    """Returns a canned PrepResult. Records what it was handed."""

    platform = "indeed"

    def __init__(self, result=None, raises=None):
        self.result = result
        self.raises = raises
        self.calls = []

    def can_handle(self, vacancy):
        return True

    def inspect_apply_flow(self, vacancy, session_state_path):
        self.calls.append((vacancy.id, session_state_path))
        if self.raises is not None:
            raise self.raises
        return self.result

    def submit(self, vacancy, session_state_path):  # pragma: no cover - never called
        raise AssertionError("prep must never call submit()")


def question(text="Location", field_type=FieldType.TEXT, position=0, **kwargs):
    return ExtractedQuestion(
        question_text=text,
        field_type=field_type,
        step_url=STEP_URL,
        position=position,
        **kwargs,
    )


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "career.db"

    conn = init_vacancy_db(path)
    insert_vacancy(
        conn,
        Vacancy(
            company="Utopia",
            title="Project Engineer",
            url=INDEED_URL,
            platform="indeed",
            status="approved",
        ),
    )
    conn.close()

    conn = init_profile_db(path)
    upsert_profile(
        conn,
        CandidateProfile(
            name="Tebello Lelosa",
            region="Gauteng",
            email="test@example.com",
            phone="+27 00 000 0000",
            skills=["Maintenance planning"],
            experience=[
                ExperienceEntry(
                    title="Operations Foreman",
                    company="Fan Movement",
                    start_date="2019-01",
                )
            ],
            target_titles=[TitleLane(title="Operations Manager", primary=True)],
        ),
    )
    conn.close()

    init_submission_db(path).close()
    return path


@pytest.fixture
def vacancy(db_path):
    conn = init_vacancy_db(db_path)
    try:
        return get_by_id(conn, 1)
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def saved_session(tmp_path, monkeypatch):
    """Every test gets a saved session unless it explicitly removes it.

    A Chrome profile directory since 2026-08-08, not a storageState file —
    `Default/` is what Chrome writes on first run, and what distinguishes a real
    profile from a directory nobody has signed into.
    """
    profile = tmp_path / ".session" / "chrome-profile"
    (profile / "Default").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SESSION_STATE_PATH", str(profile))
    return profile


@pytest.fixture(autouse=True)
def no_real_drafting(monkeypatch):
    """Drafting is drafting.py's tested behaviour; prep only orchestrates it."""
    monkeypatch.setattr(
        "src.submission.prep.draft_answer",
        lambda text, sensitivity, profile, vacancy: f"draft for {text}",
    )


class TestStatusGate:
    """B1: prep acts only on the statuses submit acts on."""

    @pytest.mark.parametrize("status", ["new", "scored", "asset_ready", "rejected"])
    def test_refuses_anything_before_the_approval_gate(
        self, status, db_path, vacancy, monkeypatch
    ):
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE vacancies SET status = ? WHERE id = 1", (status,))
        conn.commit()
        conn.close()

        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=None)
        )

        with pytest.raises(SubmissionNotAllowedError):
            run_prep(vacancy, db_path=db_path)

    def test_refusal_writes_no_prep_row(self, db_path, vacancy, monkeypatch):
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE vacancies SET status = 'new' WHERE id = 1")
        conn.commit()
        conn.close()

        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=None)
        )

        with pytest.raises(SubmissionNotAllowedError):
            run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            assert get_latest_prep(conn, 1) is None
        finally:
            conn.close()


class TestPreconditions:
    """States that are about this machine, not about the posting."""

    def test_no_adapter_raises_and_writes_no_row(self, db_path, vacancy, monkeypatch):
        monkeypatch.setattr("src.submission.prep.get_adapter", lambda v: None)

        with pytest.raises(PrepNotSupportedError):
            run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            assert get_latest_prep(conn, 1) is None
        finally:
            conn.close()

    def test_missing_session_raises_and_writes_no_row(
        self, db_path, vacancy, saved_session, monkeypatch
    ):
        # A prep row describes the posting. "Never logged in" describes this
        # machine, and recording it as session_expired would make the gate tell
        # Tebello to re-run prep-submission when the fix is the login setup.
        shutil.rmtree(saved_session)
        adapter = FakeAdapter(result=None)
        monkeypatch.setattr("src.submission.prep.get_adapter", lambda v: adapter)

        with pytest.raises(SessionSetupRequiredError):
            run_prep(vacancy, db_path=db_path)

        assert adapter.calls == []
        conn = init_submission_db(db_path)
        try:
            assert get_latest_prep(conn, 1) is None
        finally:
            conn.close()


class TestQuestionPersistence:
    def test_extracted_questions_are_stored_against_this_prep(
        self, db_path, vacancy, monkeypatch
    ):
        result = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="3 questions",
            step_url=STEP_URL,
            questions=(
                question("Location", FieldType.TEXT, 0),
                question("Describe a recent project", FieldType.TEXTAREA, 1),
                question(
                    "Notice period",
                    FieldType.SELECT,
                    2,
                    options=["Immediate", "1 month"],
                    required=True,
                ),
            ),
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        prep = run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            stored = get_questions_for_prep(conn, prep.id)
        finally:
            conn.close()

        assert [q.question_text for q in stored] == [
            "Location",
            "Describe a recent project",
            "Notice period",
        ]
        assert all(q.prep_id == prep.id for q in stored)
        assert stored[2].options == ["Immediate", "1 month"]
        assert stored[2].required is True

    def test_every_question_starts_pending(self, db_path, vacancy, monkeypatch):
        # Hard Rule 1 extended to generated answers: nothing this system wrote
        # reaches an employer without Tebello having seen that specific text.
        result = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(
                question(),
                question("Describe a project", FieldType.TEXTAREA, 1),
            ),
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        prep = run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            stored = get_questions_for_prep(conn, prep.id)
        finally:
            conn.close()

        assert all(q.decision is QuestionDecision.PENDING for q in stored)
        assert all(q.final_answer is None for q in stored)

    def test_fingerprints_match_the_documented_computation(
        self, db_path, vacancy, monkeypatch
    ):
        extracted = question(
            "Notice period", FieldType.SELECT, 0, options=["1 month"], required=True
        )
        result = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(extracted,),
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        prep = run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            stored = get_questions_for_prep(conn, prep.id)
        finally:
            conn.close()

        assert stored[0].fingerprint == compute_fingerprint(
            "Notice period", FieldType.SELECT, True, ["1 month"]
        )

    def test_a_re_prep_does_not_mix_question_sets(self, db_path, vacancy, monkeypatch):
        first = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(question("Old question"),),
        )
        second = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(question("New question"),),
        )

        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=first)
        )
        first_prep = run_prep(vacancy, db_path=db_path)

        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=second)
        )
        second_prep = run_prep(vacancy, db_path=db_path)

        assert first_prep.id != second_prep.id
        conn = init_submission_db(db_path)
        try:
            assert [
                q.question_text for q in get_questions_for_prep(conn, first_prep.id)
            ] == ["Old question"]
            assert [
                q.question_text for q in get_questions_for_prep(conn, second_prep.id)
            ] == ["New question"]
        finally:
            conn.close()


class TestSensitivityAndDrafting:
    def test_sensitive_questions_are_classified_and_left_undrafted(
        self, db_path, vacancy, monkeypatch
    ):
        # A11 end to end: prep classifies, and drafting.py refuses. The real
        # draft_answer is put back rather than undoing every monkeypatch —
        # monkeypatch.undo() would also revert the autouse session fixture, and
        # the test would then fail for a reason that has nothing to do with A11.
        from src.submission import drafting

        monkeypatch.setattr("src.submission.prep.draft_answer", drafting.draft_answer)
        result = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(
                question("What is your expected salary?", FieldType.TEXT, 0),
                question(
                    "Are you authorized to work in South Africa?", FieldType.TEXT, 1
                ),
            ),
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )
        monkeypatch.setattr(
            "src.submission.drafting.run_claude_code",
            lambda *a, **k: pytest.fail("a sensitive question was sent for drafting"),
        )

        prep = run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            stored = get_questions_for_prep(conn, prep.id)
        finally:
            conn.close()

        assert stored[0].sensitivity is Sensitivity.COMPENSATION
        assert stored[1].sensitivity is Sensitivity.WORK_AUTHORIZATION
        assert all(q.drafted_answer is None for q in stored)

    def test_ordinary_questions_get_their_draft_stored(
        self, db_path, vacancy, monkeypatch
    ):
        result = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(question("Describe a recent project", FieldType.TEXTAREA, 0),),
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        prep = run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            stored = get_questions_for_prep(conn, prep.id)
        finally:
            conn.close()

        assert stored[0].sensitivity is Sensitivity.ORDINARY
        assert stored[0].drafted_answer == "draft for Describe a recent project"

    def test_a_throttled_draft_still_persists_the_question(
        self, db_path, vacancy, monkeypatch
    ):
        # A9: a throttle costs the draft, not the extraction. If the question
        # were lost, Tebello would have to re-run a live browser walkthrough to
        # recover from a transient subscription limit.
        monkeypatch.setattr("src.submission.prep.draft_answer", lambda *a, **k: None)
        result = PrepResult(
            status=PrepStatus.QUESTIONS_EXTRACTED,
            detail="",
            step_url=STEP_URL,
            questions=(question("Describe a recent project", FieldType.TEXTAREA, 0),),
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        prep = run_prep(vacancy, db_path=db_path)

        assert prep.status is PrepStatus.QUESTIONS_EXTRACTED
        conn = init_submission_db(db_path)
        try:
            stored = get_questions_for_prep(conn, prep.id)
        finally:
            conn.close()

        assert len(stored) == 1
        assert stored[0].drafted_answer is None
        assert stored[0].decision is QuestionDecision.PENDING


class TestFailureOutcomes:
    @pytest.mark.parametrize(
        "status",
        [
            PrepStatus.EXTERNAL_ATS,
            PrepStatus.CAPTCHA_DETECTED,
            PrepStatus.SESSION_EXPIRED,
            PrepStatus.UNSUPPORTED_FORM,
        ],
    )
    def test_a_failed_walkthrough_is_recorded_with_its_reason(
        self, status, db_path, vacancy, monkeypatch
    ):
        result = PrepResult(status=status, detail="why it stopped", step_url=STEP_URL)
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        prep = run_prep(vacancy, db_path=db_path)

        assert prep.status is status
        assert prep.detail == "why it stopped"
        assert prep.step_url == STEP_URL

    def test_an_adapter_exception_becomes_an_error_row(
        self, db_path, vacancy, monkeypatch
    ):
        # Same reasoning as pipeline._decide()'s adapter guard: an adapter bug is
        # data, not a traceback in Tebello's face — and it must leave a row, or
        # the vacancy looks never-prepped and the gate says the wrong thing.
        monkeypatch.setattr(
            "src.submission.prep.get_adapter",
            lambda v: FakeAdapter(raises=RuntimeError("selector vanished")),
        )

        prep = run_prep(vacancy, db_path=db_path)

        assert prep.status is PrepStatus.ERROR
        assert "selector vanished" in prep.detail

    def test_no_questions_is_a_success_and_unblocks_submit(
        self, db_path, vacancy, monkeypatch
    ):
        result = PrepResult(
            status=PrepStatus.NO_QUESTIONS,
            detail="no screening questions",
            step_url=STEP_URL,
        )
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        run_prep(vacancy, db_path=db_path)

        conn = init_submission_db(db_path)
        try:
            assert submission_prep_ready(conn, 1).ready is True
        finally:
            conn.close()


class TestPrepNeverTransitionsStatus:
    """B2: every prep outcome leaves the vacancy exactly where it was."""

    @pytest.mark.parametrize(
        "result",
        [
            PrepResult(status=PrepStatus.NO_QUESTIONS, detail=""),
            PrepResult(status=PrepStatus.EXTERNAL_ATS, detail=""),
            PrepResult(status=PrepStatus.CAPTCHA_DETECTED, detail=""),
            PrepResult(
                status=PrepStatus.QUESTIONS_EXTRACTED,
                detail="",
                questions=(
                    ExtractedQuestion(
                        question_text="Location",
                        field_type=FieldType.TEXT,
                        step_url=STEP_URL,
                        position=0,
                    ),
                ),
            ),
        ],
    )
    def test_status_is_unchanged(self, result, db_path, vacancy, monkeypatch):
        monkeypatch.setattr(
            "src.submission.prep.get_adapter", lambda v: FakeAdapter(result=result)
        )

        run_prep(vacancy, db_path=db_path)

        conn = init_vacancy_db(db_path)
        try:
            assert get_by_id(conn, 1).status == "approved"
        finally:
            conn.close()


class TestAdaptersNeverTouchTheDatabase:
    """B3, enforced by what the adapter is handed rather than by convention."""

    def test_the_adapter_receives_only_the_session_path(
        self, db_path, vacancy, monkeypatch
    ):
        adapter = FakeAdapter(
            result=PrepResult(status=PrepStatus.NO_QUESTIONS, detail="")
        )
        monkeypatch.setattr("src.submission.prep.get_adapter", lambda v: adapter)

        run_prep(vacancy, db_path=db_path)

        ((_, session_path),) = adapter.calls
        assert session_path.name == "chrome-profile"
