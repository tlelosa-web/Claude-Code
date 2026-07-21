from dataclasses import dataclass, field
from typing import Optional

REQUIRED_FIELDS = ("name", "region")


@dataclass
class TitleLane:
    """One candidate title lane. `weight` orders lanes relative to each
    other for matching; `primary` marks the lane the pipeline leads with."""

    title: str
    primary: bool = False
    weight: float = 1.0

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("TitleLane.title is required")
        if self.weight <= 0:
            raise ValueError(f"TitleLane.weight must be positive, got {self.weight}")


@dataclass
class ExperienceEntry:
    title: str
    company: str
    start_date: str
    end_date: Optional[str] = None
    description: str = ""

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("ExperienceEntry.title is required")
        if not self.company or not self.company.strip():
            raise ValueError("ExperienceEntry.company is required")
        if not self.start_date or not self.start_date.strip():
            raise ValueError("ExperienceEntry.start_date is required")


@dataclass
class CandidateProfile:
    name: str
    region: str
    skills: list[str] = field(default_factory=list)
    experience: list[ExperienceEntry] = field(default_factory=list)
    target_titles: list[TitleLane] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    salary_floor: Optional[int] = None
    id: Optional[int] = None

    def __post_init__(self):
        for f in REQUIRED_FIELDS:
            val = getattr(self, f)
            if not val or not str(val).strip():
                raise ValueError(f"Missing required field: {f}")

        if not self.skills:
            raise ValueError("At least one skill is required")

        if not self.experience:
            raise ValueError("At least one experience entry is required")

        if not self.target_titles:
            raise ValueError("At least one target_titles lane is required")

        primary_count = sum(1 for lane in self.target_titles if lane.primary)
        if primary_count != 1:
            raise ValueError(
                f"Exactly one target_titles lane must be flagged primary, found {primary_count}"
            )

        if self.salary_floor is not None and self.salary_floor < 0:
            raise ValueError(f"salary_floor must be non-negative, got {self.salary_floor}")

    @property
    def primary_title(self) -> TitleLane:
        return next(lane for lane in self.target_titles if lane.primary)

    @classmethod
    def from_dict(cls, data: dict) -> "CandidateProfile":
        return cls(
            name=data["name"],
            region=data["region"],
            skills=list(data.get("skills", [])),
            experience=[ExperienceEntry(**e) for e in data.get("experience", [])],
            target_titles=[TitleLane(**t) for t in data.get("target_titles", [])],
            industries=list(data.get("industries", [])),
            salary_floor=data.get("salary_floor"),
        )
