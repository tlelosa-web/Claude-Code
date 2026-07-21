import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from .migrations import apply_migrations
from .schema import Vacancy

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "career.db"


def _vacancy_from_row(row: sqlite3.Row) -> Vacancy:
    return Vacancy(
        id=row["id"],
        company=row["company"],
        title=row["title"],
        url=row["url"],
        description=row["description"],
        platform=row["platform"],
        salary=row["salary"],
        deadline=row["deadline"],
        scraped_at=row["scraped_at"],
        status=row["status"],
        score=row["score"],
        strengths=json.loads(row["strengths"]) if row["strengths"] is not None else None,
        weaknesses=json.loads(row["weaknesses"]) if row["weaknesses"] is not None else None,
        recommendation=row["recommendation"],
    )


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT DEFAULT '',
            platform TEXT NOT NULL,
            salary TEXT,
            deadline TEXT,
            scraped_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            UNIQUE(company, title, url)
        )
    """)
    conn.commit()
    apply_migrations(conn)
    return conn


def insert_vacancy(conn: sqlite3.Connection, vacancy: Vacancy) -> Optional[int]:
    """Insert a vacancy; returns the new row id, or None if it's a
    duplicate on (company, title, url) — re-scraping the same listing
    on a later fetch is the expected case, not an error."""
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO vacancies
            (company, title, url, description, platform, salary, deadline, scraped_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vacancy.company,
            vacancy.title,
            vacancy.url,
            vacancy.description,
            vacancy.platform,
            vacancy.salary,
            vacancy.deadline,
            vacancy.scraped_at,
            vacancy.status,
        ),
    )
    conn.commit()
    return cursor.lastrowid if cursor.rowcount > 0 else None


def get_by_status(conn: sqlite3.Connection, status: str) -> List[Vacancy]:
    rows = conn.execute(
        "SELECT * FROM vacancies WHERE status = ? ORDER BY id", (status,)
    ).fetchall()
    return [_vacancy_from_row(r) for r in rows]


def get_by_id(conn: sqlite3.Connection, vacancy_id: int) -> Optional[Vacancy]:
    row = conn.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,)).fetchone()
    if row is None:
        return None
    return _vacancy_from_row(row)


VALID_TRANSITIONS = {
    "new": {"scored"},
    "scored": {"asset_ready"},
    "asset_ready": {"approved", "rejected"},
    "approved": set(),
    "rejected": set(),
}


def update_vacancy_status(conn: sqlite3.Connection, vacancy_id: int, status: str) -> None:
    row = conn.execute(
        "SELECT status FROM vacancies WHERE id = ?", (vacancy_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Vacancy {vacancy_id} not found")

    current = row["status"]
    if status not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} → {status}")

    conn.execute("UPDATE vacancies SET status = ? WHERE id = ?", (status, vacancy_id))
    conn.commit()


def save_match_result(
    conn: sqlite3.Connection,
    vacancy_id: int,
    score: int,
    strengths: List[str],
    weaknesses: List[str],
    recommendation: str,
) -> None:
    """Persist a matching pass's result onto the vacancy record (ADR-003
    §2 — no new table). Does not touch `status`; the pipeline transitions
    that separately via `update_vacancy_status`."""
    conn.execute(
        """
        UPDATE vacancies
        SET score = ?, strengths = ?, weaknesses = ?, recommendation = ?
        WHERE id = ?
        """,
        (score, json.dumps(strengths), json.dumps(weaknesses), recommendation, vacancy_id),
    )
    conn.commit()
