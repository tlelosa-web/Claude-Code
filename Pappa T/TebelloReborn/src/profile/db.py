import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .migrations import apply_migrations
from .schema import CandidateProfile, ExperienceEntry, TitleLane

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "career.db"

_PROFILE_ID = 1


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # email/phone are in the baseline as well as in migrations 5/6 on purpose.
    # The migrations exist for databases created before this column pair; the
    # baseline exists for new ones. The shared runner's ADD COLUMN rule stops
    # the two colliding — it skips a column that already exists and records the
    # migration as applied anyway (ADR-004 §3). Belt-and-braces now rather than
    # load-bearing: the ledger no longer lets one module's versions strand
    # another's, which is what this duplication originally worked around.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidate_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            skills TEXT NOT NULL,
            experience TEXT NOT NULL,
            target_titles TEXT NOT NULL,
            industries TEXT NOT NULL,
            salary_floor INTEGER
        )
    """)
    conn.commit()
    apply_migrations(conn)
    return conn


def upsert_profile(conn: sqlite3.Connection, profile: CandidateProfile) -> None:
    conn.execute(
        """
        INSERT INTO candidate_profile
            (id, name, region, email, phone, skills, experience, target_titles,
             industries, salary_floor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            region = excluded.region,
            email = excluded.email,
            phone = excluded.phone,
            skills = excluded.skills,
            experience = excluded.experience,
            target_titles = excluded.target_titles,
            industries = excluded.industries,
            salary_floor = excluded.salary_floor
        """,
        (
            _PROFILE_ID,
            profile.name,
            profile.region,
            profile.email,
            profile.phone,
            json.dumps(profile.skills),
            json.dumps([asdict(e) for e in profile.experience]),
            json.dumps([asdict(t) for t in profile.target_titles]),
            json.dumps(profile.industries),
            profile.salary_floor,
        ),
    )
    conn.commit()


def get_profile(conn: sqlite3.Connection) -> Optional[CandidateProfile]:
    row = conn.execute(
        "SELECT * FROM candidate_profile WHERE id = ?", (_PROFILE_ID,)
    ).fetchone()
    if row is None:
        return None

    try:
        skills = json.loads(row["skills"])
        experience = [ExperienceEntry(**e) for e in json.loads(row["experience"])]
        target_titles = [TitleLane(**t) for t in json.loads(row["target_titles"])]
        industries = json.loads(row["industries"])
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            f"candidate_profile row {row['id']} contains malformed JSON"
        ) from exc

    # Migrations 5/6 add these columns but cannot back-fill them — only Tebello
    # has the values. A row written before those migrations therefore reads NULL
    # here, and CandidateProfile would reject it with a bare "Missing required
    # field: email" that says nothing about the fix.
    if not row["email"] or not row["phone"]:
        raise ValueError(
            f"candidate_profile row {row['id']} predates the contact-details "
            "migration (email/phone are empty). Re-run: "
            "career-engine import-profile --file data/profile_seed.json"
        )

    return CandidateProfile(
        id=row["id"],
        name=row["name"],
        region=row["region"],
        email=row["email"],
        phone=row["phone"],
        skills=skills,
        experience=experience,
        target_titles=target_titles,
        industries=industries,
        salary_floor=row["salary_floor"],
    )
