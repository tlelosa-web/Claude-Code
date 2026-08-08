"""RED: src/profile/schema.py doesn't exist yet — these imports must fail first."""

import pytest

from src.profile.schema import (
    REQUIRED_FIELDS,
    CandidateProfile,
    ExperienceEntry,
    TitleLane,
)

EMAIL = "tlelosa@gmail.com"
PHONE = "078 481 8711"


def _experience():
    return [
        ExperienceEntry(
            title="Operations Foreman",
            company="FanMovement (Pty) Ltd",
            start_date="2025-10",
            end_date=None,
            description="Supervise daily production and workshop operations.",
        )
    ]


class TestCandidateProfileValidation:
    def test_valid_profile_with_single_primary_lane(self):
        profile = CandidateProfile(
            name="Tebello Lelosa",
            region="Gauteng, South Africa",
            email=EMAIL,
            phone=PHONE,
            skills=["Production Planning", "SOX Compliance"],
            experience=_experience(),
            target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            industries=["Manufacturing"],
            salary_floor=45000,
        )

        assert profile.primary_title.title == "Operations Foreman"

    def test_two_lanes_one_primary_validates(self):
        profile = CandidateProfile(
            name="Tebello Lelosa",
            region="Gauteng, South Africa",
            email=EMAIL,
            phone=PHONE,
            skills=["Production Planning"],
            experience=_experience(),
            target_titles=[
                TitleLane(title="Operations Foreman/Manager", primary=True, weight=1.0),
                TitleLane(
                    title="Project Engineer (Mechanical)", primary=False, weight=0.6
                ),
            ],
            industries=["Manufacturing"],
        )

        assert profile.primary_title.title == "Operations Foreman/Manager"
        assert len(profile.target_titles) == 2

    def test_missing_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            CandidateProfile(
                name="",
                region="Gauteng",
                email=EMAIL,
                phone=PHONE,
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_region_raises(self):
        with pytest.raises(ValueError, match="region"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="",
                email=EMAIL,
                phone=PHONE,
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_skills_raises(self):
        with pytest.raises(ValueError, match="skill"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone=PHONE,
                skills=[],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_experience_raises(self):
        with pytest.raises(ValueError, match="experience"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone=PHONE,
                skills=["x"],
                experience=[],
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_no_primary_lane_raises(self):
        with pytest.raises(ValueError, match="primary"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone=PHONE,
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=False)],
            )

    def test_multiple_primary_lanes_raises(self):
        with pytest.raises(ValueError, match="primary"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone=PHONE,
                skills=["x"],
                experience=_experience(),
                target_titles=[
                    TitleLane(title="Operations Foreman", primary=True),
                    TitleLane(title="Project Engineer", primary=True),
                ],
            )

    def test_negative_salary_floor_raises(self):
        with pytest.raises(ValueError, match="salary_floor"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone=PHONE,
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
                salary_floor=-1,
            )


class TestContactDetailsRequired:
    """Phase A (indeed-submit-adapter.md §Amendment A5): email and phone are
    nullable in SQLite — `ALTER TABLE ADD COLUMN NOT NULL` without a default is
    rejected outright, and no migration can back-fill values only Tebello has.
    The Python layer is therefore the only thing enforcing presence, so it has
    to be strict."""

    def test_required_fields_includes_email_and_phone(self):
        assert "email" in REQUIRED_FIELDS
        assert "phone" in REQUIRED_FIELDS

    def test_missing_email_raises(self):
        with pytest.raises(ValueError, match="email"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email="",
                phone=PHONE,
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_phone_raises(self):
        with pytest.raises(ValueError, match="phone"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone="",
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_whitespace_only_contact_raises(self):
        with pytest.raises(ValueError, match="phone"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                email=EMAIL,
                phone="   ",
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_omitting_contact_entirely_raises(self):
        """Defaulting to "" rather than making these positional keeps every
        existing keyword call site constructible — validation, not the dataclass
        signature, is what rejects the omission."""
        with pytest.raises(ValueError, match="email"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )


class TestTitleLaneValidation:
    def test_empty_title_raises(self):
        with pytest.raises(ValueError):
            TitleLane(title="")

    def test_non_positive_weight_raises(self):
        with pytest.raises(ValueError):
            TitleLane(title="Operations Foreman", weight=0)


class TestExperienceEntryValidation:
    def test_missing_company_raises(self):
        with pytest.raises(ValueError):
            ExperienceEntry(
                title="Operations Foreman", company="", start_date="2025-10"
            )

    def test_missing_start_date_raises(self):
        with pytest.raises(ValueError):
            ExperienceEntry(
                title="Operations Foreman", company="FanMovement", start_date=""
            )


class TestCandidateProfileFromDict:
    def test_from_dict_round_trips(self):
        data = {
            "name": "Tebello Lelosa",
            "region": "Gauteng, South Africa",
            "email": EMAIL,
            "phone": PHONE,
            "skills": ["Production Planning"],
            "experience": [
                {
                    "title": "Operations Foreman",
                    "company": "FanMovement (Pty) Ltd",
                    "start_date": "2025-10",
                    "end_date": None,
                    "description": "Supervise production.",
                }
            ],
            "target_titles": [
                {"title": "Operations Foreman/Manager", "primary": True, "weight": 1.0},
                {
                    "title": "Project Engineer (Mechanical)",
                    "primary": False,
                    "weight": 0.6,
                },
            ],
            "industries": ["Manufacturing"],
            "salary_floor": 45000,
        }

        profile = CandidateProfile.from_dict(data)

        assert profile.primary_title.title == "Operations Foreman/Manager"
        assert profile.salary_floor == 45000
        assert profile.email == EMAIL
        assert profile.phone == PHONE

    def test_from_dict_without_contact_raises(self):
        """`from_dict` reads the seed JSON — a seed file missing contact details
        must fail at import, not silently produce a profile that can't fill an
        application form."""
        data = {
            "name": "Tebello Lelosa",
            "region": "Gauteng, South Africa",
            "skills": ["Production Planning"],
            "experience": [
                {
                    "title": "Operations Foreman",
                    "company": "FanMovement (Pty) Ltd",
                    "start_date": "2025-10",
                }
            ],
            "target_titles": [
                {"title": "Operations Foreman/Manager", "primary": True, "weight": 1.0}
            ],
            "industries": ["Manufacturing"],
        }

        with pytest.raises(ValueError, match="email"):
            CandidateProfile.from_dict(data)
