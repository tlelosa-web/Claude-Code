from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AssetType(Enum):
    INSIGHT_DOC = "insight_doc"
    PAIN_POINT_SUMMARY = "pain_point_summary"
    QUICK_WIN = "quick_win"


@dataclass
class AssetResult:
    lead_id: int
    asset_text: str
    asset_type: AssetType
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
