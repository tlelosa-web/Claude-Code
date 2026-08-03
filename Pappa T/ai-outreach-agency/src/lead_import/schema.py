from dataclasses import dataclass, field
from datetime import date
from typing import Optional

VALID_SOURCES = {"apollo", "manual", "referral"}
VALID_STATUSES = {"new", "researched", "asset_ready", "approved", "drafted", "sent", "rejected"}

REQUIRED_FIELDS = {"company_name", "contact_name", "contact_title", "email"}


@dataclass
class Lead:
    company_name: str
    contact_name: str
    contact_title: str
    email: str
    id: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    region: str = "Gauteng"
    employee_count: Optional[int] = None
    source: str = "manual"
    import_date: str = field(default_factory=lambda: date.today().isoformat())
    status: str = "new"
    campaign: str = "default"

    def __post_init__(self):
        for f in REQUIRED_FIELDS:
            val = getattr(self, f)
            if not val or not val.strip():
                raise ValueError(f"Missing required field: {f}")

        self.email = self.email.strip().lower()
        if "@" not in self.email or "." not in self.email.split("@")[-1]:
            raise ValueError(f"Invalid email format: {self.email}")

        if self.source not in VALID_SOURCES:
            raise ValueError(f"Invalid source '{self.source}', must be one of {VALID_SOURCES}")

        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}', must be one of {VALID_STATUSES}")

        if self.employee_count is not None:
            self.employee_count = int(self.employee_count)
