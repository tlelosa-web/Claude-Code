"""RED: src/review/schema.py doesn't exist yet — these imports must fail
first. Mirrors ai-outreach-agency/src/approval/schema.py's Decision/
ApprovalResult shape."""

from src.review.schema import Decision, ReviewResult


class TestDecision:
    def test_approved_value(self):
        assert Decision.APPROVED.value == "approved"

    def test_rejected_value(self):
        assert Decision.REJECTED.value == "rejected"

    def test_edited_value(self):
        assert Decision.EDITED.value == "edited"


class TestReviewResult:
    def test_approved_result_defaults(self):
        result = ReviewResult(vacancy_id=1, decision=Decision.APPROVED)

        assert result.vacancy_id == 1
        assert result.decision == Decision.APPROVED
        assert result.edited_cv_text is None
        assert result.edited_cover_letter_text is None
        assert result.decided_at

    def test_edited_result_carries_edited_text(self):
        result = ReviewResult(
            vacancy_id=1,
            decision=Decision.EDITED,
            edited_cv_text="# Edited CV",
            edited_cover_letter_text="Edited cover letter",
        )

        assert result.edited_cv_text == "# Edited CV"
        assert result.edited_cover_letter_text == "Edited cover letter"
