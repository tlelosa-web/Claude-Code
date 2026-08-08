"""RED: data/profile_seed.json doesn't exist yet — reading it must fail first."""

import json
from pathlib import Path

from src.profile.schema import CandidateProfile

SEED_PATH = Path(__file__).parent.parent.parent / "data" / "profile_seed.json"
MASTER_CV_PATH = (
    Path(__file__).parent.parent.parent / "data" / "Tebello_Lelosa_Master_CV_2026.md"
)


def _load_profile() -> CandidateProfile:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return CandidateProfile.from_dict(data)


class TestProfileSeedData:
    def test_seed_file_loads_and_validates(self):
        profile = _load_profile()

        assert profile.name
        assert profile.region
        assert profile.skills
        assert profile.experience
        assert profile.industries

    def test_experience_timeline_spans_career(self):
        profile = _load_profile()

        # 19+ years of experience per CLAUDE.md's target candidate profile —
        # more than a token one- or two-job stub.
        assert len(profile.experience) >= 5

    def test_operations_foreman_is_primary_lane(self):
        profile = _load_profile()

        primary = profile.primary_title
        assert (
            "Operations Foreman" in primary.title
            or "Operations Manager" in primary.title
        )

    def test_project_engineer_present_as_secondary_lane(self):
        profile = _load_profile()

        secondary_titles = [t.title for t in profile.target_titles if not t.primary]
        assert any("Project Engineer" in t for t in secondary_titles)

    def test_salary_floor_set(self):
        profile = _load_profile()

        assert profile.salary_floor == 45000

    def test_region_is_gauteng(self):
        profile = _load_profile()

        assert "Gauteng" in profile.region


class TestSeedContactDetails:
    """Phase A (indeed-submit-adapter.md §Amendment A5). These two values are
    what Stage 6 types into Indeed's application form, so they have to be real
    and they have to agree with the CV attached to the same application."""

    def test_contact_details_are_present_and_plausible(self):
        profile = _load_profile()

        assert "@" in profile.email and "." in profile.email.split("@")[-1]
        assert sum(ch.isdigit() for ch in profile.phone) >= 9

    def test_contact_details_match_the_master_cv(self):
        """An employer sees both at once. If the seed and the CV ever disagree,
        the application contradicts itself — and nothing else in the pipeline
        would notice, since the CV is authored by hand and the form is filled
        from the database."""
        profile = _load_profile()
        cv_text = MASTER_CV_PATH.read_text(encoding="utf-8")

        assert (
            profile.email in cv_text
        ), f"seed email {profile.email!r} does not appear in the Master CV"
        cv_digits = "".join(ch for ch in cv_text if ch.isdigit())
        seed_digits = "".join(ch for ch in profile.phone if ch.isdigit())
        assert (
            seed_digits in cv_digits
        ), f"seed phone {profile.phone!r} does not appear in the Master CV"
