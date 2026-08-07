"""Stage 6 CLI dispatch — `career-engine submit`.

Mirrors tests/unit/test_review_cli.py: the stage owns its CLI module, so the
patches target src.submission.cli.<name> rather than src.main.<name>. Argument
parsing itself stays in tests/unit/test_main.py, where build_parser lives.

Every test drives the real main() entry point so dispatch is exercised end to
end; only the submission pipeline and the DB reads are mocked.
"""

from unittest.mock import patch

import pytest

from src.main import main
from src.submission.pipeline import SubmissionNotAllowedError, SubmissionStatusError
from src.submission.schema import (
    SubmissionAttempt,
    SubmissionMethod,
    SubmissionOutcome,
)
from src.vacancy_search.schema import Vacancy


@pytest.fixture(autouse=True)
def _tmp_db_path(tmp_path, monkeypatch):
    """No dispatch test may touch the real project career.db."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "career.db"))


def _make_vacancy(**overrides) -> Vacancy:
    defaults = dict(
        company="Acme Engineering", title="Operations Foreman", url="https://x"
    )
    defaults.update(overrides)
    v = Vacancy(**defaults)
    v.id = overrides.get("id", 1)
    return v


def _attempt(outcome, vacancy_id=7, method=SubmissionMethod.AUTO) -> SubmissionAttempt:
    attempt = SubmissionAttempt(
        vacancy_id=vacancy_id, method=method, outcome=outcome, detail="detail"
    )
    attempt.id = 1
    return attempt


class TestDispatchSubmit:
    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_dispatches_to_run_submission(self, mock_get_by_id, mock_run_submission):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])

        mock_run_submission.assert_called_once()
        assert mock_run_submission.call_args.kwargs["manual"] is False

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_manual_flag_is_passed_through(self, mock_get_by_id, mock_run_submission):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(
            SubmissionOutcome.SUBMITTED, method=SubmissionMethod.MANUAL
        )

        main(["submit", "--vacancy-id", "7", "--manual"])

        assert mock_run_submission.call_args.kwargs["manual"] is True

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_missing_vacancy_exits_without_dispatch(
        self, mock_get_by_id, mock_run_submission
    ):
        mock_get_by_id.return_value = None

        with pytest.raises(SystemExit):
            main(["submit", "--vacancy-id", "99"])

        mock_run_submission.assert_not_called()

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_not_supported_output_tells_the_operator_what_to_do(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        """Stable substrings, asserted. "Clear message" is otherwise untestable
        and can regress silently (spec Amendment A5)."""
        mock_get_by_id.return_value = _make_vacancy(
            id=7, url="https://example.com/job/7", status="approved"
        )
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])

        out = capsys.readouterr().out
        assert "7" in out
        assert "https://example.com/job/7" in out
        assert "submit this one by hand" in out

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_not_supported_does_not_exit_non_zero(
        self, mock_get_by_id, mock_run_submission
    ):
        """Every vacancy is not_supported in this build — a non-zero exit would
        make normal operation look broken."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])  # must not raise SystemExit

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_failed_outcome_exits_non_zero(self, mock_get_by_id, mock_run_submission):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.FAILED)

        with pytest.raises(SystemExit) as exc_info:
            main(["submit", "--vacancy-id", "7"])

        assert exc_info.value.code != 0

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_single_run_is_not_a_batch(self, mock_get_by_id, mock_run_submission):
        """The A15 refusal is scoped to --all; an explicit id is exactly the
        thing it asks for, so it must not be refused too."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])

        assert mock_run_submission.call_args.kwargs["batch"] is False

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_pending_review_output_names_the_next_command(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        """pending_review and not_supported both leave the vacancy at approved,
        so the only thing separating them for Tebello is this wording: run a
        command, versus submit it by hand."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        attempt = _attempt(SubmissionOutcome.PENDING_REVIEW)
        attempt.detail = (
            "never prepped — run `career-engine prep-submission --vacancy-id 7`"
        )
        mock_run_submission.return_value = attempt

        main(["submit", "--vacancy-id", "7"])

        out = capsys.readouterr().out
        assert "prep-submission" in out
        assert "submit this one by hand" not in out
        # Falling through to the else branch would print the detail under a
        # "FAILED" label — right words, wrong verdict, and exactly the kind of
        # near-miss that passes a substring assertion for the wrong reason.
        assert "FAILED" not in out

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_pending_review_does_not_exit_non_zero(
        self, mock_get_by_id, mock_run_submission
    ):
        """It is the ordinary state of an un-prepped application, not a failure —
        the same reasoning that keeps not_supported at exit 0."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.PENDING_REVIEW)

        main(["submit", "--vacancy-id", "7"])  # must not raise SystemExit

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_gate_refusal_is_reported_not_traced(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="asset_ready")
        mock_run_submission.side_effect = SubmissionNotAllowedError(
            "Vacancy 7 has status 'asset_ready'"
        )

        with pytest.raises(SystemExit) as exc_info:
            main(["submit", "--vacancy-id", "7"])

        assert exc_info.value.code != 0
        assert "asset_ready" in capsys.readouterr().out

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_id")
    def test_status_error_reports_what_was_recorded(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        """The split-brain case: attempt on file, status not advanced. The
        operator has to be told that precisely (spec Amendment B5)."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.side_effect = SubmissionStatusError(
            _attempt(SubmissionOutcome.SUBMITTED),
            "Attempt recorded for vacancy 7, but the status could not advance",
        )

        with pytest.raises(SystemExit) as exc_info:
            main(["submit", "--vacancy-id", "7"])

        assert exc_info.value.code != 0
        assert "Attempt recorded" in capsys.readouterr().out


class TestDispatchSubmitAll:
    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_processes_every_approved_vacancy(
        self, mock_get_by_status, mock_run_submission
    ):
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
        ]
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--all"])

        assert mock_get_by_status.call_args.args[1] == "approved"
        assert mock_run_submission.call_count == 2

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_continues_past_a_failing_vacancy(
        self, mock_get_by_status, mock_run_submission
    ):
        """One bad posting must not abandon the rest of the batch."""
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
            _make_vacancy(id=3, url="https://z", status="approved"),
        ]
        mock_run_submission.side_effect = [
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
            SubmissionStatusError(_attempt(SubmissionOutcome.FAILED), "boom"),
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
        ]

        with pytest.raises(SystemExit):
            main(["submit", "--all"])

        assert mock_run_submission.call_count == 3

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_prints_a_summary(self, mock_get_by_status, mock_run_submission, capsys):
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
        ]
        mock_run_submission.side_effect = [
            _attempt(SubmissionOutcome.SUBMITTED),
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
        ]

        main(["submit", "--all"])

        out = capsys.readouterr().out
        assert "submitted: 1" in out
        assert "not supported: 1" in out

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_all_with_no_approved_vacancies_is_not_an_error(
        self, mock_get_by_status, mock_run_submission
    ):
        mock_get_by_status.return_value = []

        main(["submit", "--all"])

        mock_run_submission.assert_not_called()

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_all_marks_every_run_as_a_batch(
        self, mock_get_by_status, mock_run_submission
    ):
        """Amendment A15's refusal is enforced in the pipeline, where the attempt
        is recorded — the CLI's whole job is to say which kind of run this is."""
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
        ]
        mock_run_submission.return_value = _attempt(SubmissionOutcome.PENDING_REVIEW)

        main(["submit", "--all"])

        assert [c.kwargs["batch"] for c in mock_run_submission.call_args_list] == [
            True,
            True,
        ]

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_summary_counts_pending_review_separately(
        self, mock_get_by_status, mock_run_submission, capsys
    ):
        """Folding it into 'not supported' would tell Tebello to submit six
        applications by hand that a single prep-submission run would unblock."""
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
            _make_vacancy(id=3, url="https://z", status="approved"),
        ]
        mock_run_submission.side_effect = [
            _attempt(SubmissionOutcome.PENDING_REVIEW),
            _attempt(SubmissionOutcome.PENDING_REVIEW),
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
        ]

        main(["submit", "--all"])

        out = capsys.readouterr().out
        assert "pending review: 2" in out
        assert "not supported: 1" in out

    @patch("src.submission.cli.run_submission")
    @patch("src.submission.cli.get_by_status")
    def test_a_pending_review_batch_exits_zero(
        self, mock_get_by_status, mock_run_submission
    ):
        """The expected shape of every --all run once an adapter exists: nothing
        auto-submits, and that is the design, not a fault."""
        mock_get_by_status.return_value = [_make_vacancy(id=1, status="approved")]
        mock_run_submission.return_value = _attempt(SubmissionOutcome.PENDING_REVIEW)

        main(["submit", "--all"])  # must not raise SystemExit
