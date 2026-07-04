import re
import sqlite3
from pathlib import Path
from typing import List, Optional

from .schema import Lead

DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "leads.db"

_LEGAL_SUFFIXES = [
    r"\(pty\)\s*ltd",
    r"pty\.?\s*ltd",
    r"proprietary\s+limited",
    r"ltd",
    r"inc",
    r"llc",
    r"cc",
    r"corp",
]
_LEGAL_SUFFIX_RE = re.compile(
    r"\s*,?\s*(?:" + "|".join(_LEGAL_SUFFIXES) + r")\.?\s*$", re.IGNORECASE
)


def normalize_company_name(name: str) -> str:
    """Lowercase, collapse whitespace, and strip a trailing legal suffix
    (Pty Ltd, CC, Inc, ...) so near-identical company names dedupe together."""
    normalized = " ".join(name.strip().lower().split())
    return _LEGAL_SUFFIX_RE.sub("", normalized).strip() or normalized


def _lead_from_row(row: sqlite3.Row) -> Lead:
    return Lead(
        id=row["id"],
        company_name=row["company_name"],
        contact_name=row["contact_name"],
        contact_title=row["contact_title"],
        email=row["email"],
        phone=row["phone"],
        website=row["website"],
        industry=row["industry"],
        region=row["region"],
        employee_count=row["employee_count"],
        source=row["source"],
        import_date=row["import_date"],
        status=row["status"],
    )


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = db_path or DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            contact_title TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            website TEXT,
            industry TEXT,
            region TEXT DEFAULT 'Gauteng',
            employee_count INTEGER,
            source TEXT DEFAULT 'manual',
            import_date TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            UNIQUE(company_name, email)
        )
    """)
    conn.commit()
    return conn


def insert_lead(conn: sqlite3.Connection, lead: Lead) -> int:
    cursor = conn.execute(
        """
        INSERT INTO leads
            (company_name, contact_name, contact_title, email, phone, website,
             industry, region, employee_count, source, import_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead.company_name,
            lead.contact_name,
            lead.contact_title,
            lead.email,
            lead.phone,
            lead.website,
            lead.industry,
            lead.region,
            lead.employee_count,
            lead.source,
            lead.import_date,
            lead.status,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def find_duplicate(conn: sqlite3.Connection, lead: Lead) -> Optional[Lead]:
    """Return an existing lead that matches on email + normalized company name, or None."""
    target_name = normalize_company_name(lead.company_name)
    rows = conn.execute(
        "SELECT * FROM leads WHERE email = ?", (lead.email,)
    ).fetchall()
    for row in rows:
        existing = _lead_from_row(row)
        if normalize_company_name(existing.company_name) == target_name:
            return existing
    return None


def get_all_leads(conn: sqlite3.Connection) -> List[Lead]:
    rows = conn.execute("SELECT * FROM leads ORDER BY id").fetchall()
    return [_lead_from_row(r) for r in rows]


def get_leads_by_status(conn: sqlite3.Connection, status: str) -> List[Lead]:
    rows = conn.execute(
        "SELECT * FROM leads WHERE status = ? ORDER BY id", (status,)
    ).fetchall()
    return [_lead_from_row(r) for r in rows]


def get_lead_by_id(conn: sqlite3.Connection, lead_id: int) -> Optional[Lead]:
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if row is None:
        return None
    return _lead_from_row(row)


VALID_TRANSITIONS = {
    "new": {"researched"},
    "researched": {"asset_ready"},
    "asset_ready": {"approved", "rejected"},
    "approved": {"drafted"},
    "drafted": set(),
    "rejected": set(),
}


def update_lead_status(lead_id: int, status: str, db_path: str | None = None) -> None:
    db = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if row is None:
            raise ValueError(f"Lead {lead_id} not found")
        current = row["status"]
        if status not in VALID_TRANSITIONS.get(current, set()):
            raise ValueError(
                f"Invalid transition: {current} → {status}"
            )
        conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        conn.commit()
    finally:
        conn.close()
