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
"""

import pytest

from src.submission.db import get_attempts_for_vacancy, init_db as init_submission_db
from src.submission.pipeline import (
    SubmissionNotAllowedError,
    SubmissionStatusError,
    run_submission,
)
from src.submission.schema import SubmissionMethod, SubmissionOutcome
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

    def test_successful_adapter_marks_submitted(self, tmp_path, registry, monkeypatch):
        monkeypatch.setattr(
            "src.submission.pipeline.session_state_available", lambda: True
        )
        registry["indeed"] = _FakeAdapter(ok=True, detail="confirmation #123")
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.SUBMITTED
        assert attempt.detail == "confirmation #123"
        assert _status(db_path, vacancy_id) == "submitted"

    def test_unsuccessful_adapter_marks_submission_failed(
        self, tmp_path, registry, monkeypatch
    ):
        monkeypatch.setattr(
            "src.submission.pipeline.session_state_available", lambda: True
        )
        registry["indeed"] = _FakeAdapter(ok=False, detail="form validation error")
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.FAILED
        assert attempt.detail == "form validation error"
        assert _status(db_path, vacancy_id) == "submission_failed"

    def test_raising_adapter_is_recorded_not_propagated(
        self, tmp_path, registry, monkeypatch
    ):
        """A crashing adapter must not take down a run-all batch, and must never
        look like a success."""
        monkeypatch.setattr(
            "src.submission.pipeline.session_state_available", lambda: True
        )
        registry["indeed"] = _FakeAdapter(raises=RuntimeError("selector not found"))
        db_path = tmp_path / "career.db"
        vacancy_id = _seed(db_path)

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

        attempt = run_submission(_vacancy(db_path, vacancy_id), db_path=db_path)

        assert attempt.outcome == SubmissionOutcome.FAILED
        assert "login setup" in attempt.detail
        assert adapter.calls == []


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
