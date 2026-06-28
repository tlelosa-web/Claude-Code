from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DraftResult:
    lead_id: int
    gmail_draft_id: str
    subject: str
    body_preview: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
