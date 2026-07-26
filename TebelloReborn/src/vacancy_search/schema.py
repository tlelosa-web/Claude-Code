from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

VALID_PLATFORMS = {"indeed", "linkedin"}
VALID_STATUSES = {"new", "scored", "asset_ready", "approved", "rejected"}
REQUIRED_FIELDS = ("company", "title", "url")


@dataclass
class Vacancy:
    company: str
    title: str
    url: str
    id: Optional[int] = None
    description: str = ""
    platform: str = "indeed"
    salary: Optional[str] = None
    deadline: Optional[str] = None
    scraped_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: str = "new"
    score: Optional[int] = None
    strengths: Optional[list[str]] = None
    weaknesses: Optional[list[str]] = None
    recommendation: Optional[str] = None
    # Transient, in-memory only — NOT persisted to SQLite (the PDF export is
    # already the durable artifact; storing full text again would be pure
    # bloat). Set by run_doc_gen() so main.py's `run` command can hand the
    # exact generated text to the human review gate without a second
    # generation round-trip. No migration needed — see doc_gen/pipeline.py.
    cv_text: Optional[str] = None
    cover_letter_text: Optional[str] = None

    def __post_init__(self):
        for f in REQUIRED_FIELDS:
            val = getattr(self, f)
            if not val or not val.strip():
                raise ValueError(f"Missing required field: {f}")

        if self.platform not in VALID_PLATFORMS:
            raise ValueError(
                f"Invalid platform '{self.platform}', must be one of {VALID_PLATFORMS}"
            )

        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}', must be one of {VALID_STATUSES}"
            )

        if self.score is not None and not (0 <= self.score <= 100):
            raise ValueError(f"score must be between 0 and 100, got {self.score}")
