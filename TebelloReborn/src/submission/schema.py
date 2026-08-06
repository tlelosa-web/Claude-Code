from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SubmissionMethod(Enum):
    AUTO = "auto"
    MANUAL = "manual"


class SubmissionOutcome(Enum):
    SUBMITTED = "submitted"
    FAILED = "failed"
    # No adapter can handle this vacancy — it is still Tebello's to submit by
    # hand, so the vacancy deliberately stays at 'approved' (spec §Outcome →
    # status mapping). Not an error state.
    NOT_SUPPORTED = "not_supported"


@dataclass
class SubmissionAttempt:
    """One recorded attempt to submit an approved application.

    `submissions` is an append-only attempt log — several rows per vacancy are
    expected (a `not_supported` followed later by a manual submission is the
    ordinary path in this build). `vacancies.status` is current state; this is
    history (spec Amendment B4).
    """

    vacancy_id: int
    method: SubmissionMethod
    outcome: SubmissionOutcome
    detail: Optional[str] = None
    # Timezone-aware, matching ReviewResult.decided_at and Vacancy.scraped_at.
    # A naive utcnow() string sorts inconsistently against those (Amendment A8).
    attempted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    id: Optional[int] = None

    def __post_init__(self):
        # A raw string would pass the dataclass untouched and only fail later at
        # the DB CHECK constraint — a long way from the code that got it wrong.
        if not isinstance(self.method, SubmissionMethod):
            raise TypeError(
                f"method must be a SubmissionMethod, got {type(self.method).__name__}"
            )

        if not isinstance(self.outcome, SubmissionOutcome):
            raise TypeError(
                f"outcome must be a SubmissionOutcome, got {type(self.outcome).__name__}"
            )
