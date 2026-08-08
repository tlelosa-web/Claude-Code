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

from src.submission.schema import (
    FieldType,
    PrepReadiness,
    PrepStatus,
    QuestionDecision,
    ScreeningQuestion,
    Sensitivity,
    SubmissionAttempt,
    SubmissionMethod,
    SubmissionOutcome,
    SubmissionPrep,
)


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

    def test_pending_review_value(self):
        """Phase B, spec Amendment A3. Deliberately distinct from
        not_supported: conflating "no automated path exists" with "an automated
        path exists and is one command away" would hide real progress from the
        operator and from any Stage 7 reader counting rows."""
        assert SubmissionOutcome.PENDING_REVIEW.value == "pending_review"

    def test_prep_failed_was_never_added(self):
        """Spec Amendment A3 resolved the referenced-but-undefined `prep_failed`
        by deletion, not definition: prep does not attempt a submission, so its
        failures belong in submission_preps, not in an attempt log."""
        assert not hasattr(SubmissionOutcome, "PREP_FAILED")
        assert "prep_failed" not in {o.value for o in SubmissionOutcome}


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


class TestPrepStatus:
    """Spec Amendment A2. Seven states, because "prep never ran" and "prepped,
    genuinely zero questions" are both zero screening_questions rows and only
    one of them is submittable — inferring state from an absence of rows is the
    bug this enum exists to remove."""

    def test_values(self):
        assert {s.value for s in PrepStatus} == {
            "questions_extracted",
            "no_questions",
            "external_ats",
            "captcha_detected",
            "session_expired",
            "unsupported_form",
            "error",
        }


class TestFieldType:
    def test_values(self):
        """`radio` is present per A12 — `checkbox` was carrying too many
        meanings, and the recon found yes/no questions rendered as free text, so
        the control cannot be inferred from the question's wording."""
        assert {f.value for f in FieldType} == {
            "text",
            "textarea",
            "select",
            "checkbox",
            "radio",
            "file",
        }


class TestQuestionDecision:
    def test_values(self):
        assert {d.value for d in QuestionDecision} == {
            "pending",
            "approved",
            "edited",
            "rejected",
        }


class TestSensitivity:
    def test_values(self):
        """A11: work-authorization, compensation and demographic questions are
        never LLM-drafted at all — the draft would anchor the answer."""
        assert {s.value for s in Sensitivity} == {
            "ordinary",
            "compensation",
            "work_authorization",
            "demographic",
        }

    def test_ordinary_is_the_default_classification(self):
        assert Sensitivity.ORDINARY.value == "ordinary"


class TestSubmissionPrep:
    def test_defaults(self):
        prep = SubmissionPrep(vacancy_id=3, status=PrepStatus.NO_QUESTIONS)

        assert prep.vacancy_id == 3
        assert prep.status == PrepStatus.NO_QUESTIONS
        assert prep.detail is None
        assert prep.step_url is None
        assert prep.id is None

    def test_prepped_at_is_timezone_aware(self):
        """Same reasoning as SubmissionAttempt.attempted_at (A8) — a naive
        string sorts inconsistently against every other *_at in this database."""
        prep = SubmissionPrep(vacancy_id=1, status=PrepStatus.ERROR)

        parsed = datetime.fromisoformat(prep.prepped_at)
        assert parsed.tzinfo is not None

    def test_rejects_raw_string_status(self):
        with pytest.raises(TypeError):
            SubmissionPrep(vacancy_id=1, status="no_questions")


def _question(**overrides) -> ScreeningQuestion:
    kwargs = {
        "vacancy_id": 1,
        "prep_id": 1,
        "question_text": "Describe a recent project you led.",
        "field_type": FieldType.TEXTAREA,
        "step_url": "https://za.indeed.com/apply/questions",
        "position": 0,
        "fingerprint": "a" * 64,
    }
    kwargs.update(overrides)
    return ScreeningQuestion(**kwargs)


class TestScreeningQuestion:
    def test_defaults(self):
        question = _question()

        assert question.field_key is None
        assert question.required is False
        assert question.options is None
        assert question.sensitivity == Sensitivity.ORDINARY
        assert question.drafted_answer is None
        assert question.final_answer is None
        assert question.decision == QuestionDecision.PENDING
        assert question.decided_at is None
        assert question.id is None

    def test_starts_pending_never_pre_approved(self):
        """Hard Rule 1's principle extended to new content: nothing this system
        generates reaches an employer without Tebello having seen that text."""
        assert _question(drafted_answer="A drafted answer.").decision == (
            QuestionDecision.PENDING
        )

    def test_extracted_at_is_timezone_aware(self):
        parsed = datetime.fromisoformat(_question().extracted_at)
        assert parsed.tzinfo is not None

    def test_rejects_raw_string_field_type(self):
        with pytest.raises(TypeError):
            _question(field_type="textarea")

    def test_rejects_raw_string_decision(self):
        with pytest.raises(TypeError):
            _question(decision="approved")

    def test_rejects_raw_string_sensitivity(self):
        with pytest.raises(TypeError):
            _question(sensitivity="ordinary")

    def test_accepts_options_on_a_choice_field(self):
        question = _question(field_type=FieldType.SELECT, options=["Yes", "No"])

        assert question.options == ["Yes", "No"]

    def test_rejects_options_on_a_free_text_field(self):
        """A12: options_json is NULL for free-text types. Options on a textarea
        means the extractor mis-read the control, and a drift fingerprint built
        from them would compare the wrong thing."""
        with pytest.raises(ValueError):
            _question(field_type=FieldType.TEXTAREA, options=["Yes", "No"])

    def test_rejects_options_on_a_file_field(self):
        with pytest.raises(ValueError):
            _question(field_type=FieldType.FILE, options=["CV.pdf"])


class TestPrepReadiness:
    """The structured answer submission_prep_ready() returns — A2 renamed
    all_questions_reviewed() because the old name described half the check."""

    def test_ready_carries_no_outcome(self):
        readiness = PrepReadiness(ready=True, outcome=None, reason="")

        assert readiness.ready is True
        assert readiness.outcome is None

    def test_not_ready_carries_the_outcome_to_record(self):
        readiness = PrepReadiness(
            ready=False,
            outcome=SubmissionOutcome.PENDING_REVIEW,
            reason="run prep-submission",
        )

        assert readiness.ready is False
        assert readiness.outcome == SubmissionOutcome.PENDING_REVIEW
        assert readiness.reason == "run prep-submission"

    def test_ready_with_an_outcome_is_a_contradiction(self):
        """pipeline.py records `outcome` only when `ready` is False — a truthy
        pair would silently log an attempt outcome for a vacancy that proceeded."""
        with pytest.raises(ValueError):
            PrepReadiness(
                ready=True, outcome=SubmissionOutcome.NOT_SUPPORTED, reason="x"
            )

    def test_not_ready_without_an_outcome_is_a_contradiction(self):
        with pytest.raises(ValueError):
            PrepReadiness(ready=False, outcome=None, reason="x")
