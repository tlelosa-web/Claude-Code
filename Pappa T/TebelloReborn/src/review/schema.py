from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Decision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


@dataclass
class ReviewResult:
    vacancy_id: int
    decision: Decision
    edited_cv_text: Optional[str] = None
    edited_cover_letter_text: Optional[str] = None
    decided_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
