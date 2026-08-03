import sqlite3
from typing import Optional

from src.approval.db import init_approvals_table
from src.lead_import.schema import VALID_STATUSES


def get_status_counts(conn: sqlite3.Connection, campaign: Optional[str] = None) -> dict[str, int]:
    counts = {status: 0 for status in VALID_STATUSES}
    if campaign:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM leads WHERE campaign = ? GROUP BY status",
            (campaign,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT status, COUNT(*) AS n FROM leads GROUP BY status").fetchall()
    for row in rows:
        counts[row["status"]] = row["n"]
    return counts


def get_campaign_matrix(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    rows = conn.execute(
        "SELECT campaign, status, COUNT(*) AS n FROM leads GROUP BY campaign, status"
    ).fetchall()
    matrix: dict[str, dict[str, int]] = {}
    for row in rows:
        campaign_counts = matrix.setdefault(row["campaign"], {status: 0 for status in VALID_STATUSES})
        campaign_counts[row["status"]] = row["n"]
    return matrix


def get_approval_history(conn: sqlite3.Connection) -> list[dict]:
    init_approvals_table(conn)
    rows = conn.execute(
        """
        SELECT approvals.decision, approvals.decided_at, approvals.edited_asset_text,
               leads.company_name
        FROM approvals
        JOIN leads ON leads.id = approvals.lead_id
        ORDER BY approvals.decided_at DESC
        """
    ).fetchall()
    return [
        {
            "company_name": row["company_name"],
            "decision": row["decision"],
            "decided_at": row["decided_at"],
            "edited": row["edited_asset_text"] is not None,
        }
        for row in rows
    ]


def get_summary(conn: sqlite3.Connection) -> dict:
    counts = get_status_counts(conn)
    total_leads = sum(counts.values())
    decided = counts["approved"] + counts["rejected"] + counts["drafted"]
    approval_rate = (counts["approved"] + counts["drafted"]) / decided if decided else 0.0
    return {
        "total_leads": total_leads,
        "approved": counts["approved"],
        "rejected": counts["rejected"],
        "drafted": counts["drafted"],
        "approval_rate": approval_rate,
    }
