"""RED: src/profile/db.py doesn't exist yet — these imports must fail first."""

import sqlite3

import pytest

from src.profile.db import get_profile, init_db, upsert_profile
from src.profile.migrations import MIGRATIONS
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane

EMAIL = "tlelosa@gmail.com"
PHONE = "078 481 8711"


def _profile(name: str = "Tebello Lelosa") -> CandidateProfile:
    return CandidateProfile(
        name=name,
        region="Gauteng, South Africa",
        email=EMAIL,
        phone=PHONE,
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

    def test_upsert_then_get_round_trips_contact_details(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        upsert_profile(conn, _profile())

        loaded = get_profile(conn)

        assert loaded.email == EMAIL
        assert loaded.phone == PHONE
        conn.close()

    def test_upsert_updates_contact_details_in_place(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        upsert_profile(conn, _profile())

        changed = _profile()
        changed.email = "new.address@example.com"
        changed.phone = "011 555 0100"
        upsert_profile(conn, changed)

        loaded = get_profile(conn)

        assert loaded.email == "new.address@example.com"
        assert loaded.phone == "011 555 0100"
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


class TestContactDetailMigrations:
    """Phase A (indeed-submit-adapter.md §Amendment A5). These are the first
    migrations this project has written since Hard Rule 6 was recorded, and the
    rule's whole point is that the obvious version numbers (1 and 2) would be
    silently skipped forever on the live database."""

    def test_migration_versions_are_globally_unique_and_at_least_five(self):
        versions = [version for version, _ in MIGRATIONS]

        assert versions == [5, 6], (
            "profile migrations must start at 5 — vacancy_search owns 1-4 on the "
            "same shared PRAGMA user_version (CLAUDE.md Hard Rule 6)"
        )

    def test_init_db_creates_email_and_phone_columns(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(candidate_profile)")
        }

        assert "email" in columns
        assert "phone" in columns
        conn.close()

    def test_migrations_apply_to_a_database_already_at_version_four(self, tmp_path):
        """The live `career.db` sits at user_version = 4 with the pre-contact
        schema. This reproduces it exactly: had these migrations been numbered
        1 and 2, `apply_migrations`' `if version > current` would skip both
        without error and `upsert_profile` would die on `no such column: email`."""
        db_path = tmp_path / "career.db"
        legacy = sqlite3.connect(str(db_path))
        legacy.execute("""
            CREATE TABLE candidate_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                region TEXT NOT NULL,
                skills TEXT NOT NULL,
                experience TEXT NOT NULL,
                target_titles TEXT NOT NULL,
                industries TEXT NOT NULL,
                salary_floor INTEGER
            )
        """)
        legacy.execute("PRAGMA user_version = 4")
        legacy.commit()
        legacy.close()

        conn = init_db(db_path)

        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(candidate_profile)")
        }
        assert "email" in columns
        assert "phone" in columns
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 6

        # and the migrated table is actually writable through the normal path
        upsert_profile(conn, _profile())
        assert get_profile(conn).email == EMAIL
        conn.close()

    def test_migrations_are_idempotent_across_repeated_init(self, tmp_path):
        db_path = tmp_path / "career.db"
        init_db(db_path).close()

        conn = init_db(db_path)

        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(candidate_profile)")
        }
        assert {"email", "phone"} <= columns
        conn.close()

    def test_fresh_database_does_not_advance_the_shared_user_version(self, tmp_path):
        """A fresh database gets email/phone from the baseline CREATE TABLE, so
        migrations 5/6 have nothing to do and must NOT bump the counter.

        `import-profile` is the documented first command, so if it advanced a
        brand-new database to 6, vacancy_search's migrations 1-4 would be
        skipped forever — its `vacancies` baseline omits those columns, so they
        would exist nowhere at all."""
        conn = init_db(tmp_path / "career.db")

        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        conn.close()


class TestSharedUserVersionOrdering:
    """Regression lock for a bug this phase introduced and the integration
    suite caught: profile's migrations are numbered above vacancy_search's, and
    every module gates on the same PRAGMA user_version."""

    def test_import_profile_first_does_not_strand_vacancy_migrations(self, tmp_path):
        """CLAUDE.md documents `import-profile` as the first command and
        `fetch-vacancies` as the second. In that order, profile's init_db used
        to advance a fresh database to 6, so vacancy_search's migrations 1-4
        were skipped and `vacancies` came out with no `score` column — an
        IndexError on the first read, on every new install."""
        from src.vacancy_search.db import init_db as init_vacancy_db

        db_path = tmp_path / "career.db"

        init_db(db_path).close()
        conn = init_vacancy_db(db_path)

        columns = {row[1] for row in conn.execute("PRAGMA table_info(vacancies)")}

        assert {"score", "strengths", "weaknesses", "recommendation"} <= columns
        conn.close()

    def test_either_init_order_converges_on_the_same_schema(self, tmp_path):
        from src.vacancy_search.db import init_db as init_vacancy_db

        def _columns(db_path, first, second):
            first(db_path).close()
            conn = second(db_path)
            result = {
                table: {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
                for table in ("candidate_profile", "vacancies")
            }
            conn.close()
            return result

        profile_first = _columns(tmp_path / "a.db", init_db, init_vacancy_db)
        vacancy_first = _columns(tmp_path / "b.db", init_vacancy_db, init_db)

        assert profile_first == vacancy_first


class TestPreMigrationRowIsActionable:
    def test_row_predating_contact_columns_raises_actionable_error(self, tmp_path):
        """A real consequence of A5 that the spec doesn't name: the live
        `career.db` already holds a profile row, and the migration cannot
        back-fill values only Tebello has. So the first `get_profile()` after
        migrating reads NULL contact details and the schema layer rejects them.
        The message has to say what to do about it, not just name the field."""
        conn = init_db(tmp_path / "career.db")
        conn.execute("""
            INSERT INTO candidate_profile
                (id, name, region, skills, experience, target_titles, industries, salary_floor)
            VALUES (1, 'Tebello Lelosa', 'Gauteng', '["x"]',
                    '[{"title": "Ops", "company": "F", "start_date": "2025-10"}]',
                    '[{"title": "Ops", "primary": true, "weight": 1.0}]', '[]', NULL)
            """)
        conn.commit()

        with pytest.raises(ValueError, match="import-profile"):
            get_profile(conn)
        conn.close()


class TestMalformedData:
    def test_corrupt_json_column_raises(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        conn.execute("""
            INSERT INTO candidate_profile
                (id, name, region, skills, experience, target_titles, industries, salary_floor)
            VALUES (1, 'Broken', 'Gauteng', 'not-json', '[]', '[]', '[]', NULL)
            """)
        conn.commit()

        with pytest.raises(ValueError, match="candidate_profile"):
            get_profile(conn)
        conn.close()
