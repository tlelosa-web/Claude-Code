from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ResearchResult:
    lead_id: int
    summary: str
    raw_data: dict
    researched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
