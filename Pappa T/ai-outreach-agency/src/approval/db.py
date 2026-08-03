import sqlite3
from pathlib import Path
from typing import Optional

from .schema import ApprovalResult, Decision

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "leads.db"


def init_approvals_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            decision TEXT NOT NULL,
            edited_asset_text TEXT,
            decided_at TEXT NOT NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    conn.commit()


def save_approval(
    conn: sqlite3.Connection,
    result: ApprovalResult,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO approvals (lead_id, decision, edited_asset_text, decided_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            result.lead_id,
            result.decision.value,
            result.edited_asset_text,
            result.decided_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid
