import json
import subprocess
from dataclasses import dataclass
from typing import Optional

from .schema import GenerationStatus

DEFAULT_RUNNER_TIMEOUT_SECONDS = 120
ALLOWED_TOOLS = "Read,Write"

_THROTTLE_INDICATORS = ("rate limit", "quota", "usage limit", "throttle")


@dataclass
class RunnerResult:
    status: GenerationStatus
    result_text: Optional[str] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None


def run_claude_code(
    instruction: str, timeout: int = DEFAULT_RUNNER_TIMEOUT_SECONDS
) -> RunnerResult:
    """Shell out to headless Claude Code (`claude -p`) to generate a
    document. Failures are data, not exceptions (ADR-003 §3) — only a
    missing `claude` binary (FileNotFoundError) propagates uncaught."""
    try:
        completed = subprocess.run(
            [
                "claude",
                "-p",
                instruction,
                "--allowedTools",
                ALLOWED_TOOLS,
                "--output-format",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunnerResult(
            status=GenerationStatus.ERROR,
            error_message=f"claude -p timed out after {timeout}s",
        )

    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stderr_lower = stderr.lower()
        if any(indicator in stderr_lower for indicator in _THROTTLE_INDICATORS):
            return RunnerResult(status=GenerationStatus.THROTTLED, error_message=stderr)
        return RunnerResult(status=GenerationStatus.ERROR, error_message=stderr)

    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return RunnerResult(
            status=GenerationStatus.ERROR,
            error_message=f"Could not parse claude -p output as JSON: {exc}",
        )

    return RunnerResult(
        status=GenerationStatus.SUCCESS,
        result_text=parsed.get("result"),
        session_id=parsed.get("session_id"),
        duration_ms=parsed.get("duration_ms"),
        cost_usd=parsed.get("total_cost_usd", parsed.get("cost_usd")),
    )
