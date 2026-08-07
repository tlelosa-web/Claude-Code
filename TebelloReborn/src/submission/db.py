import sqlite3
from pathlib import Path
from typing import List, Optional

from .schema import SubmissionAttempt, SubmissionMethod, SubmissionOutcome

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "career.db"

# This module has no migrations.py yet, for the ordinary reason: `submissions`
# is a net-new table, so its CREATE TABLE belongs in init_db() per this
# project's convention (docs/todo.md Resolved Items), and nothing has changed
# it since.
#
# The *original* reason was different and no longer applies. Every module used
# to share one global `PRAGMA user_version`, so an empty stub here invited a
# future `(1, ...)` entry that would be skipped forever against a live database
# already at version 4. ADR-004 replaced the counter with a per-module ledger,
# so adding a migrations.py here starting at version 1 is now correct and safe
# — which is exactly what Phase B does.
# See docs/specs/submission-core.md §Migration Note and ADR-004.


def _attempt_from_row(row: sqlite3.Row) -> SubmissionAttempt:
    return SubmissionAttempt(
        id=row["id"],
        vacancy_id=row["vacancy_id"],
        method=SubmissionMethod(row["method"]),
        outcome=SubmissionOutcome(row["outcome"]),
        detail=row["detail"],
        attempted_at=row["attempted_at"],
    )


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Per-connection in SQLite, not a property of the schema — it has to be set
    # on every connection that writes, which is why save_attempt's callers get
    # their connection from here and nowhere else.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL REFERENCES vacancies(id),
            method TEXT NOT NULL CHECK (method IN ('auto','manual')),
            outcome TEXT NOT NULL CHECK (outcome IN ('submitted','failed','not_supported')),
            detail TEXT,
            attempted_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_attempt(conn: sqlite3.Connection, attempt: SubmissionAttempt) -> int:
    """Persist one submission attempt. Append-only — several rows per vacancy
    are expected (a `not_supported` followed later by a manual submission is the
    ordinary path in this build)."""
    cursor = conn.execute(
        """
        INSERT INTO submissions
            (vacancy_id, method, outcome, detail, attempted_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            attempt.vacancy_id,
            attempt.method.value,
            attempt.outcome.value,
            attempt.detail,
            attempt.attempted_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_attempts_for_vacancy(
    conn: sqlite3.Connection, vacancy_id: int
) -> List[SubmissionAttempt]:
    """Newest first. `vacancies.status` is current state; this is history — a
    reader must not treat an older `not_supported` row as the current one."""
    rows = conn.execute(
        "SELECT * FROM submissions WHERE vacancy_id = ? ORDER BY id DESC",
        (vacancy_id,),
    ).fetchall()
    return [_attempt_from_row(r) for r in rows]
