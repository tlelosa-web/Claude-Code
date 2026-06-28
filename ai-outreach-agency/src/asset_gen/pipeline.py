import logging

from src.lead_import.db import update_lead_status
from src.lead_import.schema import Lead
from src.research.schema import ResearchResult
from .generator import generate_asset
from .schema import AssetResult, AssetType

logger = logging.getLogger(__name__)


def run_asset_gen(
    lead: Lead,
    research: ResearchResult,
    asset_type: AssetType = AssetType.INSIGHT_DOC,
    db_path: str | None = None,
) -> AssetResult:
    result = generate_asset(lead, research, asset_type=asset_type)
    logger.info("Generated %s for lead %s", result.asset_type.value, result.lead_id)
    update_lead_status(lead.id, "asset_ready", db_path)
    return result
