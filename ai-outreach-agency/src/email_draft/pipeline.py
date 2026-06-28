from src.lead_import.schema import Lead
from src.approval.schema import ApprovalResult, Decision
from src.asset_gen.schema import AssetResult
from .composer import compose_email
from .gmail_client import GmailClient
from .schema import DraftResult


def run_email_draft(
    lead: Lead,
    approval: ApprovalResult,
    asset: AssetResult,
    gmail: GmailClient | None = None,
) -> DraftResult:
    if approval.decision not in (Decision.APPROVED, Decision.EDITED):
        raise ValueError("Cannot draft email without approval")

    if approval.decision == Decision.EDITED and approval.edited_asset_text:
        asset_text = approval.edited_asset_text
    else:
        asset_text = asset.asset_text

    gmail = gmail or GmailClient()
    email = compose_email(lead, asset_text)
    draft_id = gmail.create_draft(email["to"], email["subject"], email["body"])

    return DraftResult(
        lead_id=lead.id,
        gmail_draft_id=draft_id,
        subject=email["subject"],
        body_preview=email["body"][:100],
    )
