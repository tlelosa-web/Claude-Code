"""RED: src/doc_gen/runner.py doesn't exist yet — these imports must fail first."""

import json
import subprocess
from unittest.mock import patch

import pytest

from src.doc_gen.runner import (
    DEFAULT_RUNNER_TIMEOUT_SECONDS,
    RunnerResult,
    run_claude_code,
)
from src.doc_gen.schema import GenerationStatus


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


class TestRunClaudeCodeCommandShape:
    @patch("src.doc_gen.runner.subprocess.run")
    def test_invokes_expected_command(self, mock_run):
        mock_run.return_value = _completed(stdout=json.dumps({"result": "ok"}))

        run_claude_code("Generate a CV for this vacancy.")

        args, kwargs = mock_run.call_args
        assert args[0] == [
            "claude",
            "-p",
            "Generate a CV for this vacancy.",
            "--allowedTools",
            "Read,Write",
            "--output-format",
            "json",
        ]
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["timeout"] == DEFAULT_RUNNER_TIMEOUT_SECONDS

    @patch("src.doc_gen.runner.subprocess.run")
    def test_custom_timeout_is_passed_through(self, mock_run):
        mock_run.return_value = _completed(stdout=json.dumps({"result": "ok"}))

        run_claude_code("instruction", timeout=30)

        assert mock_run.call_args.kwargs["timeout"] == 30


class TestRunClaudeCodeSuccess:
    @patch("src.doc_gen.runner.subprocess.run")
    def test_success_parses_json_result_fields(self, mock_run):
        mock_run.return_value = _completed(
            stdout=json.dumps(
                {
                    "result": "# Tailored CV\n...",
                    "session_id": "sess-abc",
                    "duration_ms": 4200,
                    "total_cost_usd": 0.012,
                }
            )
        )

        result = run_claude_code("Generate a CV.")

        assert isinstance(result, RunnerResult)
        assert result.status == GenerationStatus.SUCCESS
        assert result.result_text == "# Tailored CV\n..."
        assert result.session_id == "sess-abc"
        assert result.duration_ms == 4200
        assert result.cost_usd == 0.012

    @patch("src.doc_gen.runner.subprocess.run")
    def test_malformed_json_on_success_exit_is_error(self, mock_run):
        mock_run.return_value = _completed(stdout="not json")

        result = run_claude_code("Generate a CV.")

        assert result.status == GenerationStatus.ERROR
        assert result.error_message is not None


class TestRunClaudeCodeTimeout:
    @patch("src.doc_gen.runner.subprocess.run")
    def test_timeout_expired_returns_error_result(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)

        result = run_claude_code("Generate a CV.")

        assert result.status == GenerationStatus.ERROR
        assert "timed out" in result.error_message


class TestRunClaudeCodeNonZeroExit:
    @patch("src.doc_gen.runner.subprocess.run")
    def test_rate_limit_stderr_classified_as_throttled(self, mock_run):
        mock_run.return_value = _completed(
            returncode=1, stderr="Error: rate limit exceeded"
        )

        result = run_claude_code("Generate a CV.")

        assert result.status == GenerationStatus.THROTTLED
        assert "rate limit" in result.error_message.lower()

    @patch("src.doc_gen.runner.subprocess.run")
    def test_generic_failure_stderr_classified_as_error(self, mock_run):
        mock_run.return_value = _completed(returncode=1, stderr="Error: something broke")

        result = run_claude_code("Generate a CV.")

        assert result.status == GenerationStatus.ERROR
        assert "something broke" in result.error_message


class TestRunClaudeCodeMissingBinary:
    @patch("src.doc_gen.runner.subprocess.run")
    def test_missing_claude_binary_propagates(self, mock_run):
        mock_run.side_effect = FileNotFoundError("claude not found")

        with pytest.raises(FileNotFoundError):
            run_claude_code("Generate a CV.")
