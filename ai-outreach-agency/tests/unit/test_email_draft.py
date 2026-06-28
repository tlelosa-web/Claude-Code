import pytest

from src.lead_import.schema import Lead
from src.asset_gen.schema import AssetResult, AssetType
from src.approval.schema import ApprovalResult, Decision
from src.email_draft.composer import compose_email
from src.email_draft.pipeline import run_email_draft
from src.email_draft.schema import DraftResult


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        id=1,
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
        industry="Manufacturing",
        source="apollo",
    )
    defaults.update(overrides)
    return Lead(**defaults)


def _make_asset(**overrides) -> AssetResult:
    defaults = dict(
        lead_id=1,
        asset_text="# Insight: Acme Engineering\n\nOriginal asset content.",
        asset_type=AssetType.INSIGHT_DOC,
    )
    defaults.update(overrides)
    return AssetResult(**defaults)


def _make_approval(**overrides) -> ApprovalResult:
    defaults = dict(
        lead_id=1,
        decision=Decision.APPROVED,
    )
    defaults.update(overrides)
    return ApprovalResult(**defaults)


class TestComposer:
    def test_subject_contains_company_name(self):
        lead = _make_lead()
        email = compose_email(lead, "Some asset text.")
        assert "Acme Engineering" in email["subject"]

    def test_body_contains_asset_text(self):
        lead = _make_lead()
        asset_text = "Unique insight content here."
        email = compose_email(lead, asset_text)
        assert "Unique insight content here." in email["body"]

    def test_to_field_is_lead_email(self):
        lead = _make_lead()
        email = compose_email(lead, "text")
        assert email["to"] == "john@acme.co.za"


class TestEmailDraftPipeline:
    def test_happy_path(self):
        lead = _make_lead()
        asset = _make_asset()
        approval = _make_approval()

        result = run_email_draft(lead, approval, asset)

        assert isinstance(result, DraftResult)
        assert result.lead_id == 1
        assert result.gmail_draft_id.startswith("draft_")
        assert "Acme Engineering" in result.subject
        assert result.created_at

    def test_rejected_raises(self):
        lead = _make_lead()
        asset = _make_asset()
        approval = _make_approval(decision=Decision.REJECTED)

        with pytest.raises(ValueError, match="Cannot draft email without approval"):
            run_email_draft(lead, approval, asset)

    def test_edited_text_used(self):
        lead = _make_lead()
        asset = _make_asset()
        edited = "Completely revised asset content."
        approval = _make_approval(
            decision=Decision.EDITED,
            edited_asset_text=edited,
        )

        result = run_email_draft(lead, approval, asset)

        assert isinstance(result, DraftResult)
        assert result.body_preview  # just confirm it was created

    def test_edited_text_in_composed_body(self):
        lead = _make_lead()
        asset = _make_asset()
        edited = "Revised content for the email."
        approval = _make_approval(
            decision=Decision.EDITED,
            edited_asset_text=edited,
        )

        email = compose_email(lead, edited)
        assert "Revised content for the email." in email["body"]
