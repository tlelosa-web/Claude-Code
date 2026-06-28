import os

from src.lead_import.schema import Lead
from src.research.schema import ResearchResult
from src.shared.openrouter_client import call_openrouter
from .prompt_builder import build_prompt
from .schema import AssetResult, AssetType


def _stub_text(lead: Lead) -> str:
    return (
        f"# AI Automation Insight: {lead.company_name}\n\n"
        f"Based on our research, {lead.company_name} operates in the "
        f"{lead.industry or 'heavy engineering'} sector with services that "
        f"could benefit from targeted automation.\n\n"
        f"## Key Opportunity\n\n"
        f"Many firms in your sector spend significant time on manual reporting "
        f"and equipment tracking. An AI-driven system could reduce this by up "
        f"to 40%, freeing your team to focus on higher-value work.\n\n"
        f"## Next Step\n\n"
        f"I'd welcome 15 minutes to walk through how this applies specifically "
        f"to {lead.company_name}. Would next week work for a quick call?"
    )


def generate_asset(
    lead: Lead,
    research: ResearchResult,
    asset_type: AssetType = AssetType.INSIGHT_DOC,
) -> AssetResult:
    prompt = build_prompt(lead, research)

    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        text = _stub_text(lead)
    else:
        text = call_openrouter(prompt)

    return AssetResult(
        lead_id=lead.id,
        asset_text=text,
        asset_type=asset_type,
    )
