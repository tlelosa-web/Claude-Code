import sqlite3
from pathlib import Path
from typing import Optional

from .migrations import apply_migrations
from .schema import Decision, ReviewResult

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "career.db"


def _result_from_row(row: sqlite3.Row) -> ReviewResult:
    return ReviewResult(
        vacancy_id=row["vacancy_id"],
        decision=Decision(row["decision"]),
        edited_cv_text=row["edited_cv_text"],
        edited_cover_letter_text=row["edited_cover_letter_text"],
        decided_at=row["decided_at"],
    )


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
            decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','edited')),
            edited_cv_text TEXT,
            edited_cover_letter_text TEXT,
            decided_at TEXT NOT NULL
        )
    """)
    conn.commit()
    apply_migrations(conn)
    return conn


def save_approval(conn: sqlite3.Connection, result: ReviewResult) -> int:
    cursor = conn.execute(
        """
        INSERT INTO approvals
            (vacancy_id, decision, edited_cv_text, edited_cover_letter_text, decided_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            result.vacancy_id,
            result.decision.value,
            result.edited_cv_text,
            result.edited_cover_letter_text,
            result.decided_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_approval_by_vacancy_id(
    conn: sqlite3.Connection, vacancy_id: int
) -> Optional[ReviewResult]:
    row = conn.execute(
        "SELECT * FROM approvals WHERE vacancy_id = ? ORDER BY id DESC LIMIT 1",
        (vacancy_id,),
    ).fetchone()
    if row is None:
        return None
    return _result_from_row(row)
