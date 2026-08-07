"""RED: src/submission/pipeline.py doesn't exist yet — these imports must fail
first.

run_submission() is the single entry point to Stage 6 and the place CLAUDE.md
Hard Rule 1 is enforced: nothing reaches a submission path without having passed
the human approval gate. The gate admits `approved` and `submission_failed`
(retries) and refuses everything else — `submission_failed` is reachable only
from `approved`, so admitting it cannot let an unapproved application through
(docs/specs/submission-core.md Amendment A1).

Failure paths are exercised through an injected fake adapter. With the shipped
registry empty there is no way to produce a real `failed` outcome in this build,
and the tests say so rather than implying a reachable production path
(Amendment B3).

Phase C adds the prep-state gate (Amendment A2) between the adapter lookup and
the adapter's submit(). Every test below that reaches an adapter therefore has to
seed a prep row first — reaching submit() without one is now the bug, not the
setup cost.
"""

import pytest

from src.submission.db import (
    get_attempts_for_vacancy,
    init_db as init_submission_db,
    save_prep,
    save_question,
)
from src.submission.pipeline import (
    SubmissionNotAllowedError,
    SubmissionStatusError,
    run_submission,
)
from src.submission.schema import (
    FieldType,
    PrepStatus,
    QuestionDecision,
    ScreeningQuestion,
    SubmissionMethod,
    SubmissionOutcome,
    SubmissionPrep,
)
from src.vacancy_search.db import (
    get_by_id,
    init_db as init_vacancy_db,
    insert_vacancy,
    update_vacancy_status,
)
from src.vacancy_search.schema import Vacancy

_TO_APPROVED = ("scored", "asset_ready", "approved")


class _FakeAdapter:
    def __init__(self, platform="indeed", ok=True, detail="ok", raises=None):
        self.platform = platform
        self._ok = ok
        self._detail = detail
        self._raises = raises
        self.calls = []

    def can_handle(self, vacancy):
        return True

    def submit(self, vacancy, session_state_path):
        self.calls.append((vacancy.id, session_state_path))
        if self._raises is not None:
            raise self._raises
        return self._ok, self._detail


@pytest.fixture
def registry(monkeypatch):
    fake: dict = {}
    monkeypatch.setattr("src.submission.eligibility.ADAPTERS", fake)
    return fake


def _seed(db_path, status="approved", platform="indeed") -> int:
    """Insert a vacancy and walk it to `status` through the real state machine —
    never by writing the status directly, so the test can't create a state the
    pipeline could never legitimately see."""
    conn = init_vacancy_db(db_path)
    vacancy_id = insert_vacancy(
        conn,
        Vacancy(
            company="Acme",
            title="Operations Foreman",
            url="https://example.com/job/1",
            platform=platform,
        ),
    )
    for step in _TO_APPROVED:
        if get_by_id(conn, vacancy_id).status == status:
            break
        update_vacancy_status(conn, vacancy_id, step)
    conn.close()
    return vacancy_id


def _vacancy(db_path, vacancy_id) -> Vacancy:
    conn = init_vacancy_db(db_path)
    vacancy = get_by_id(conn, vacancy_id)
    conn.close()
    return vacancy


def _status(db_path, vacancy_id) -> str:
    return _vacancy(db_path, vacancy_id).status


def _attempts(db_path, vacancy_id):
    conn = init_submission_db(db_path)
    attempts = get_attempts_for_vacancy(conn, vacancy_id)
    conn.close()
    return attempts


def _prep(db_path, vacancy_id, status=PrepStatus.NO_QUESTIONS, questions=()) -> int:
    """Record one prep run, optionally with question decisions.

    `questions` is a sequence of QuestionDecision — the gate only ever looks at
    the decision, so the rest of each row is filler that satisfies the schema.
    """
    conn = init_submission_db(db_path)
    prep_id = save_prep(conn, SubmissionPrep(vacancy_id=vacancy_id, status=status))
    for position, decision in enumerate(questions):
        save_question(
            conn,
            ScreeningQuestion(
                vacancy_id=vacancy_id,
                prep_id=prep_id,
                question_text=f"Question {position}?",
                field_type=FieldType.TEXT,
                step_url="https://smartapply.indeed.com/questions",
                position=position,
                fingerprint=f"fp{position}",
                decision=decision,
                final_answer="an answer",
            ),
        )
    conn.close()
    return prep_id


@pytest.fixture
def live_session(monkeypatch):
    """The adapter path's other precondition, so a prep-gate test isn't silently
    passing for the wrong reason."""
    monkeypatch.setattr("src.submission.pipeline.session_state_available", lambda: True)


class TestApprovalGate:
    @pytest.mark.parametrize("status", ["new", "scored", "asset_ready"])
    def test_refuses_vacancy_that_never_passed_the_gate(self, tmp_path, status):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path, status=status)

        with pytest.raises(SubmissionNotAllowedError):
            run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

    def test_refuses_rejected_vacancy(self, tmp_path):
        db_path = tmp_path / "career.db"
        conn = init_vacancy_db(db_path)
        vacancy_id = insert_vacancy(
            conn, Vacancy(company="Acme", title="Foreman", url="https://x")
        )
        update_vacancy_status(conn, vacancy_id, "scored")
        update_vacancy_status(conn, vacancy_id, "asset_ready")
        update_vacancy_status(conn, vacancy_id, "rejected")
        conn.close()

        with pytest.raises(SubmissionNotAllowedError):
            run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

    def test_refusal_records_no_attempt(self, tmp_path):
        """A refused submission must leave no trace suggesting one happened."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path, status="scored")

        with pytest.raises(SubmissionNotAllowedError):
            run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert _attempts(db_path, vacancy_id) == []

    def test_accepts_approved(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED

    def test_accepts_submission_failed_for_retry(self, tmp_path):
        """The test that would have caught the spec's original contradiction:
        failures are retryable, so the gate must admit submission_failed."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        conn = init_vacancy_db(db_path)
        update_vacancy_status(conn, vacancy_id, "submission_failed")
        conn.close()

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), manual=True, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert _status(db_path, vacancy_id) == "submitted"

    def test_refuses_already_submitted(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        conn = init_vacancy_db(db_path)
        update_vacancy_status(conn, vacancy_id, "submitted")
        conn.close()

        with pytest.raises(SubmissionNotAllowedError):
            run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

    def test_missing_vacancy_raises(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed(db_path)
        ghost = Vacancy(id=999, company="Ghost", title="None", url="https://x")

        with pytest.raises(ValueError, match="not found"):
            run_submission(ghost, db_path=db_path)


class TestNoAdapterPath:
    def test_records_not_supported(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED
        assert attempt.method == SubmissionMethod.AUTO
        assert attempt.id is not None

    def test_leaves_vacancy_approved(self, tmp_path):
        """It still needs Tebello's action, so the status must keep saying so."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert _status(db_path, vacancy_id) == "approved"

    def test_detail_names_the_platform(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path, platform="pnet")

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert "pnet" in attempt.detail

    def test_declining_adapter_falls_through_to_not_supported(self, tmp_path, registry):
        class _Declining(_FakeAdapter):
            def can_handle(self, vacancy):
                return False

        registry["indeed"] = _Declining()
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED
        assert _status(db_path, vacancy_id) == "approved"


class TestManualPath:
    def test_records_manual_submission(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), manual=True, db_path=db_path
        )

        assert attempt.method == SubmissionMethod.MANUAL
        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert _status(db_path, vacancy_id) == "submitted"

    def test_detail_frames_it_as_an_operator_assertion(self, tmp_path):
        """The system cannot witness a manual submission and must not claim to
        (Amendment A9)."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), manual=True, db_path=db_path
        )

        assert "operator-asserted" in attempt.detail

    def test_manual_never_calls_an_adapter(self, tmp_path, registry):
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        run_submission(_vacancy(db_path, vacancy_id), manual=True, db_path=db_path)

        assert adapter.calls == []


class TestAdapterPath:
    """Only reachable via an injected adapter — the shipped registry is empty."""

    def test_successful_adapter_marks_submitted(self, tmp_path, registry, live_session):
        registry["indeed"] = _FakeAdapter(ok=True, detail="confirmation #123")
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert attempt.detail == "confirmation #123"
        assert _status(db_path, vacancy_id) == "submitted"

    def test_unsuccessful_adapter_marks_submission_failed(
        self, tmp_path, registry, live_session
    ):
        registry["indeed"] = _FakeAdapter(ok=False, detail="form validation error")
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.FAILED
        assert attempt.detail == "form validation error"
        assert _status(db_path, vacancy_id) == "submission_failed"

    def test_raising_adapter_is_recorded_not_propagated(
        self, tmp_path, registry, live_session
    ):
        """A crashing adapter must not take down a run-all batch, and must never
        look like a success."""
        registry["indeed"] = _FakeAdapter(raises=RuntimeError("selector not found"))
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.FAILED
        assert "selector not found" in attempt.detail
        assert _status(db_path, vacancy_id) == "submission_failed"

    def test_missing_session_state_fails_with_actionable_detail(
        self, tmp_path, registry, monkeypatch
    ):
        monkeypatch.setattr(
            "src.submission.pipeline.session_state_available", lambda: False
        )
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.FAILED
        assert "login setup" in attempt.detail
        assert adapter.calls == []


class TestPrepStateGate:
    """One test per row of Amendment A2's gate table.

    The gate reads state that prep already recorded — it never reopens a browser
    to re-derive it, which is why A1 could make can_handle() a pure predicate.
    """

    def test_never_prepped_is_pending_review(self, tmp_path, registry, live_session):
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "never prepped" in attempt.detail
        assert "prep-submission" in attempt.detail
        assert adapter.calls == []

    def test_external_ats_is_not_supported(self, tmp_path, registry, live_session):
        """An external ATS is genuinely Tebello's to submit by hand — telling him
        to re-run prep would send him round a loop that cannot succeed."""
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=PrepStatus.EXTERNAL_ATS)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED
        assert "external ATS" in attempt.detail
        assert adapter.calls == []

    @pytest.mark.parametrize(
        "status",
        [
            PrepStatus.CAPTCHA_DETECTED,
            PrepStatus.SESSION_EXPIRED,
            PrepStatus.UNSUPPORTED_FORM,
            PrepStatus.ERROR,
        ],
    )
    def test_retryable_prep_failure_is_pending_review(
        self, tmp_path, registry, live_session, status
    ):
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=status)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.PENDING_REVIEW
        assert status.value in attempt.detail
        assert adapter.calls == []

    def test_no_questions_proceeds_to_the_adapter(
        self, tmp_path, registry, live_session
    ):
        """The state that motivated the whole table: zero questions after a real
        prep is submittable, while zero questions from no prep at all is not."""
        adapter = _FakeAdapter(ok=True, detail="done")
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=PrepStatus.NO_QUESTIONS)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert [call[0] for call in adapter.calls] == [vacancy_id]

    @pytest.mark.parametrize(
        "decisions",
        [
            (QuestionDecision.APPROVED, QuestionDecision.APPROVED),
            (QuestionDecision.APPROVED, QuestionDecision.EDITED),
            (QuestionDecision.EDITED, QuestionDecision.EDITED),
        ],
    )
    def test_fully_decided_questions_proceed_to_the_adapter(
        self, tmp_path, registry, live_session, decisions
    ):
        adapter = _FakeAdapter(ok=True, detail="done")
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(
            db_path,
            vacancy_id,
            status=PrepStatus.QUESTIONS_EXTRACTED,
            questions=decisions,
        )

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert [call[0] for call in adapter.calls] == [vacancy_id]

    @pytest.mark.parametrize(
        "undecided", [QuestionDecision.PENDING, QuestionDecision.REJECTED]
    )
    def test_any_undecided_question_blocks_submission(
        self, tmp_path, registry, live_session, undecided
    ):
        """Hard Rule 1 extends to every generated word an employer reads — a
        rejected answer is as unsendable as one that was never looked at."""
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(
            db_path,
            vacancy_id,
            status=PrepStatus.QUESTIONS_EXTRACTED,
            questions=(QuestionDecision.APPROVED, undecided),
        )

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "review-questions" in attempt.detail
        assert adapter.calls == []

    def test_pending_review_leaves_the_vacancy_approved(
        self, tmp_path, registry, live_session
    ):
        """It is still Tebello's to act on, so the status must keep saying so —
        the same reasoning as not_supported, and the reason both map to None."""
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert _status(db_path, vacancy_id) == "approved"

    def test_pending_review_is_recorded_as_an_attempt(
        self, tmp_path, registry, live_session
    ):
        adapter = _FakeAdapter()
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        attempts = _attempts(db_path, vacancy_id)
        assert len(attempts) == 1
        assert attempts[0].outcome == SubmissionOutcome.PENDING_REVIEW
        assert attempts[0].method == SubmissionMethod.AUTO

    def test_gate_runs_before_the_session_check(self, tmp_path, registry, monkeypatch):
        """A recorded external-ATS finding does not become fixable by logging in,
        so a missing session must not mask it behind 'run the login setup'."""
        monkeypatch.setattr(
            "src.submission.pipeline.session_state_available", lambda: False
        )
        registry["indeed"] = _FakeAdapter()
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=PrepStatus.EXTERNAL_ATS)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED

    def test_gate_uses_the_latest_prep(self, tmp_path, registry, live_session):
        """A successful re-prep must clear an earlier failure, not be outvoted by
        it — submission_preps is append-only."""
        adapter = _FakeAdapter(ok=True, detail="done")
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=PrepStatus.CAPTCHA_DETECTED)
        _prep(db_path, vacancy_id, status=PrepStatus.NO_QUESTIONS)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.SUBMITTED

    def test_no_adapter_never_reaches_the_gate(self, tmp_path, live_session):
        """With no adapter there is nothing to prep for, so 'submit it by hand'
        stays the answer rather than 'run prep-submission' for a platform that
        has none."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path, platform="pnet")

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED
        assert "pnet" in attempt.detail

    def test_manual_bypasses_the_gate(self, tmp_path, registry, live_session):
        """--manual records something Tebello already did by hand; screening
        questions he answered himself need no review by this system."""
        registry["indeed"] = _FakeAdapter()
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), manual=True, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert _status(db_path, vacancy_id) == "submitted"


class TestBatchRefusal:
    """Amendment A15 — `--all` does not auto-submit in this build.

    A policy, not an engine: the accepted account-risk exposure is per-account,
    and six real applications in ninety seconds is a materially different risk
    from six deliberate single runs. Refusing needs no tuning and cannot be
    mis-tuned; a backoff policy can be designed later against observed behavior.
    """

    def test_batch_refuses_a_vacancy_that_would_reach_the_adapter(
        self, tmp_path, registry, live_session
    ):
        adapter = _FakeAdapter(ok=True, detail="done")
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=PrepStatus.NO_QUESTIONS)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), batch=True, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "explicit --vacancy-id" in attempt.detail
        assert adapter.calls == []
        assert _status(db_path, vacancy_id) == "approved"

    def test_single_run_is_unaffected(self, tmp_path, registry, live_session):
        adapter = _FakeAdapter(ok=True, detail="done")
        registry["indeed"] = adapter
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        _prep(db_path, vacancy_id, status=PrepStatus.NO_QUESTIONS)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), batch=False, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.SUBMITTED

    def test_batch_still_reports_the_real_gate_reason_when_there_is_one(
        self, tmp_path, registry, live_session
    ):
        """The refusal is the last word, not the first — a vacancy that isn't
        prepped should still be told to run prep-submission, since that is what
        it actually needs next."""
        registry["indeed"] = _FakeAdapter()
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), batch=True, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.PENDING_REVIEW
        assert "never prepped" in attempt.detail

    def test_batch_leaves_manual_untouched(self, tmp_path, registry, live_session):
        """A --manual --all run records submissions Tebello already made; there
        is no automated application to rate-limit."""
        registry["indeed"] = _FakeAdapter()
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), manual=True, batch=True, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.SUBMITTED

    def test_batch_still_reports_not_supported(self, tmp_path, live_session):
        """Unchanged from submission-core A6 — the refusal is scoped to vacancies
        that would really submit, not to the whole batch."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path, platform="pnet")

        attempt = run_submission(
            _vacancy(db_path, vacancy_id), batch=True, db_path=db_path
        )

        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED


class TestPersistenceOrdering:
    def test_attempt_is_committed_before_the_status_transition(
        self, tmp_path, monkeypatch
    ):
        """Fails closed: a crash after persistence leaves a recorded attempt with
        a stale status, never a submitted vacancy with no attempt on file — the
        same ordering run_review_gate uses."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        def _boom(*args, **kwargs):
            raise ValueError("transition exploded")

        monkeypatch.setattr("src.submission.pipeline.update_vacancy_status", _boom)

        with pytest.raises(SubmissionStatusError):
            run_submission(_vacancy(db_path, vacancy_id), manual=True, db_path=db_path)

        attempts = _attempts(db_path, vacancy_id)
        assert len(attempts) == 1
        assert attempts[0].outcome == SubmissionOutcome.SUBMITTED
        assert _status(db_path, vacancy_id) == "approved"

    def test_status_error_carries_the_recorded_attempt(self, tmp_path, monkeypatch):
        """So the CLI can tell the operator exactly what was recorded rather
        than printing a bare traceback."""
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)
        monkeypatch.setattr(
            "src.submission.pipeline.update_vacancy_status",
            lambda *a, **k: (_ for _ in ()).throw(ValueError("nope")),
        )

        with pytest.raises(SubmissionStatusError) as exc_info:
            run_submission(_vacancy(db_path, vacancy_id), manual=True, db_path=db_path)

        assert exc_info.value.attempt.vacancy_id == vacancy_id
        assert exc_info.value.attempt.id is not None


class TestAppendOnlyLog:
    def test_repeated_runs_append_rather_than_replace(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)
        run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert len(_attempts(db_path, vacancy_id)) == 2
