"""RED: src/profile/schema.py doesn't exist yet — these imports must fail first."""

import pytest

from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane


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
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_region_raises(self):
        with pytest.raises(ValueError, match="region"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="",
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_skills_raises(self):
        with pytest.raises(ValueError, match="skill"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                skills=[],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_missing_experience_raises(self):
        with pytest.raises(ValueError, match="experience"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                skills=["x"],
                experience=[],
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
            )

    def test_no_primary_lane_raises(self):
        with pytest.raises(ValueError, match="primary"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=False)],
            )

    def test_multiple_primary_lanes_raises(self):
        with pytest.raises(ValueError, match="primary"):
            CandidateProfile(
                name="Tebello Lelosa",
                region="Gauteng",
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
                skills=["x"],
                experience=_experience(),
                target_titles=[TitleLane(title="Operations Foreman", primary=True)],
                salary_floor=-1,
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
