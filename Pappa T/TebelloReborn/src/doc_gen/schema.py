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


@dataclass
class GenerationResult:
    """A single generator call's outcome — content on success, nothing on
    throttled/error (those carry `error_message` instead). Distinct from
    `GenerationLogEntry`: this is the in-memory return value a generator
    hands back to its caller; the log entry is what gets persisted."""

    status: GenerationStatus
    doc_type: str
    content: Optional[str] = None
    session_id: Optional[str] = None
    duration_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None
