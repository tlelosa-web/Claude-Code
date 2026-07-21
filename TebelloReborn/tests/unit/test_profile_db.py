"""RED: src/profile/db.py doesn't exist yet — these imports must fail first."""

import pytest

from src.profile.db import get_profile, init_db, upsert_profile
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane


def _profile(name: str = "Tebello Lelosa") -> CandidateProfile:
    return CandidateProfile(
        name=name,
        region="Gauteng, South Africa",
        skills=["Production Planning", "SOX Compliance"],
        experience=[
            ExperienceEntry(
                title="Operations Foreman",
                company="FanMovement (Pty) Ltd",
                start_date="2025-10",
                end_date=None,
                description="Supervise production.",
            )
        ],
        target_titles=[
            TitleLane(title="Operations Foreman/Manager", primary=True, weight=1.0),
            TitleLane(title="Project Engineer (Mechanical)", primary=False, weight=0.6),
        ],
        industries=["Manufacturing"],
        salary_floor=45000,
    )


class TestInitDb:
    def test_creates_candidate_profile_table(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_profile'"
        ).fetchall()

        assert len(tables) == 1
        conn.close()


class TestUpsertAndGetProfile:
    def test_get_profile_returns_none_when_empty(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        assert get_profile(conn) is None
        conn.close()

    def test_upsert_then_get_round_trips(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        upsert_profile(conn, _profile())

        loaded = get_profile(conn)

        assert loaded is not None
        assert loaded.name == "Tebello Lelosa"
        assert loaded.salary_floor == 45000
        assert len(loaded.target_titles) == 2
        assert loaded.primary_title.title == "Operations Foreman/Manager"
        conn.close()

    def test_upsert_replaces_not_inserts_second_row(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        upsert_profile(conn, _profile(name="Tebello Lelosa"))
        upsert_profile(conn, _profile(name="Tebello L. Updated"))

        loaded = get_profile(conn)
        count = conn.execute("SELECT COUNT(*) FROM candidate_profile").fetchone()[0]

        assert count == 1
        assert loaded.name == "Tebello L. Updated"
        conn.close()


class TestMalformedData:
    def test_corrupt_json_column_raises(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        conn.execute(
            """
            INSERT INTO candidate_profile
                (id, name, region, skills, experience, target_titles, industries, salary_floor)
            VALUES (1, 'Broken', 'Gauteng', 'not-json', '[]', '[]', '[]', NULL)
            """
        )
        conn.commit()

        with pytest.raises(ValueError, match="candidate_profile"):
            get_profile(conn)
        conn.close()
