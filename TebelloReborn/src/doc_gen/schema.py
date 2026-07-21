from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GenerationStatus(Enum):
    SUCCESS = "success"
    THROTTLED = "throttled"
    ERROR = "error"


@dataclass
class GenerationLogEntry:
    vacancy_id: int
    doc_type: str
    started_at: str
    status: GenerationStatus
    id: Optional[int] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None
