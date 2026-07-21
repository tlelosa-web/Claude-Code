import sqlite3
from pathlib import Path
from typing import List, Optional

from .migrations import apply_migrations
from .schema import GenerationLogEntry, GenerationStatus

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "career.db"


def _entry_from_row(row: sqlite3.Row) -> GenerationLogEntry:
    return GenerationLogEntry(
        id=row["id"],
        vacancy_id=row["vacancy_id"],
        doc_type=row["doc_type"],
        session_id=row["session_id"],
        started_at=row["started_at"],
        duration_ms=row["duration_ms"],
        cost_usd=row["cost_usd"],
        status=GenerationStatus(row["status"]),
        error_message=row["error_message"],
    )


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS generation_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id    INTEGER NOT NULL REFERENCES vacancies(id),
            doc_type      TEXT NOT NULL CHECK (doc_type IN ('cv','cover_letter')),
            session_id    TEXT,
            started_at    TEXT NOT NULL,
            duration_ms   INTEGER,
            cost_usd      REAL,
            status        TEXT NOT NULL CHECK (status IN ('success','throttled','error')),
            error_message TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_generation_log_vacancy_id ON generation_log(vacancy_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_generation_log_started_at ON generation_log(started_at)"
    )
    conn.commit()
    apply_migrations(conn)
    return conn


def insert_generation_log(
    conn: sqlite3.Connection,
    vacancy_id: int,
    doc_type: str,
    started_at: str,
    status: GenerationStatus,
    session_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    cost_usd: Optional[float] = None,
    error_message: Optional[str] = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO generation_log
            (vacancy_id, doc_type, session_id, started_at, duration_ms, cost_usd, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vacancy_id,
            doc_type,
            session_id,
            started_at,
            duration_ms,
            cost_usd,
            status.value,
            error_message,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_by_vacancy_id(conn: sqlite3.Connection, vacancy_id: int) -> List[GenerationLogEntry]:
    rows = conn.execute(
        "SELECT * FROM generation_log WHERE vacancy_id = ? ORDER BY id", (vacancy_id,)
    ).fetchall()
    return [_entry_from_row(r) for r in rows]
