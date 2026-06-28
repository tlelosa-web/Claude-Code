import logging

from src.lead_import.schema import Lead
from src.research.schema import ResearchResult
from .generator import generate_asset
from .schema import AssetResult, AssetType

logger = logging.getLogger(__name__)


def run_asset_gen(
    lead: Lead,
    research: ResearchResult,
    asset_type: AssetType = AssetType.INSIGHT_DOC,
) -> AssetResult:
    result = generate_asset(lead, research, asset_type=asset_type)
    logger.info("Generated %s for lead %s", result.asset_type.value, result.lead_id)
    return result
