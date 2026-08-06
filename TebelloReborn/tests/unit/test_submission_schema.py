"""RED: src/submission/schema.py doesn't exist yet — these imports must fail
first. Mirrors src/review/schema.py's Decision/ReviewResult shape, which is
this project's established enum-plus-dataclass convention.

The timezone-awareness test is deliberate (spec Amendment A8): every other
`*_at` string in this database (ReviewResult.decided_at, Vacancy.scraped_at)
is timezone-aware, and a naive datetime.utcnow() string sorts inconsistently
against them.
"""

from datetime import datetime

import pytest

from src.submission.schema import SubmissionAttempt, SubmissionMethod, SubmissionOutcome


class TestSubmissionMethod:
    def test_auto_value(self):
        assert SubmissionMethod.AUTO.value == "auto"

    def test_manual_value(self):
        assert SubmissionMethod.MANUAL.value == "manual"


class TestSubmissionOutcome:
    def test_submitted_value(self):
        assert SubmissionOutcome.SUBMITTED.value == "submitted"

    def test_failed_value(self):
        assert SubmissionOutcome.FAILED.value == "failed"

    def test_not_supported_value(self):
        assert SubmissionOutcome.NOT_SUPPORTED.value == "not_supported"


class TestSubmissionAttempt:
    def test_defaults(self):
        attempt = SubmissionAttempt(
            vacancy_id=1,
            method=SubmissionMethod.AUTO,
            outcome=SubmissionOutcome.NOT_SUPPORTED,
        )

        assert attempt.vacancy_id == 1
        assert attempt.method == SubmissionMethod.AUTO
        assert attempt.outcome == SubmissionOutcome.NOT_SUPPORTED
        assert attempt.detail is None
        assert attempt.id is None
        assert attempt.attempted_at

    def test_attempted_at_is_timezone_aware(self):
        attempt = SubmissionAttempt(
            vacancy_id=1,
            method=SubmissionMethod.MANUAL,
            outcome=SubmissionOutcome.SUBMITTED,
        )

        parsed = datetime.fromisoformat(attempt.attempted_at)
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() is not None

    def test_detail_is_carried(self):
        attempt = SubmissionAttempt(
            vacancy_id=7,
            method=SubmissionMethod.AUTO,
            outcome=SubmissionOutcome.FAILED,
            detail="form validation error",
        )

        assert attempt.detail == "form validation error"

    def test_rejects_raw_string_method(self):
        """A bare string would sail past the dataclass and only fail at the
        DB CHECK constraint — catch it at construction instead."""
        with pytest.raises(TypeError):
            SubmissionAttempt(
                vacancy_id=1,
                method="auto",
                outcome=SubmissionOutcome.SUBMITTED,
            )

    def test_rejects_raw_string_outcome(self):
        with pytest.raises(TypeError):
            SubmissionAttempt(
                vacancy_id=1,
                method=SubmissionMethod.AUTO,
                outcome="submitted",
            )
