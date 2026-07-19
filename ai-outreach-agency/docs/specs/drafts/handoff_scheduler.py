"""
handoff_scheduler.py
Gatekeeper for Claude Code headless handoff calls (asset_gen / email_draft).
Checks config/handoff_settings.json + handoff_log before allowing a run.

Usage (called by pipeline, not run standalone):
    from handoff_scheduler import can_run_now
    ok, reason = can_run_now(db_path="ai_outreach.db")
    if not ok:
        log.info(f"Handoff skipped: {reason}")
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SETTINGS_PATH = Path("config/handoff_settings.json")

WEEKDAY_MAP = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        raise FileNotFoundError(f"Missing settings file: {SETTINGS_PATH}")
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def can_run_now(db_path: str) -> tuple[bool, str]:
    """Returns (allowed: bool, reason: str)."""
    settings = load_settings()
    now = datetime.now()
    today_name = WEEKDAY_MAP[now.weekday()]

    if today_name not in settings["run_days"]:
        return False, f"{today_name} not in run_days {settings['run_days']}"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    start_of_week = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    cur.execute(
        "SELECT COUNT(*) as c FROM handoff_log WHERE started_at >= ? AND status = 'success'",
        (start_of_week.isoformat(),),
    )
    weekly_count = cur.fetchone()["c"]
    if weekly_count >= settings["weekly_lead_cap"]:
        conn.close()
        return False, f"weekly cap reached ({weekly_count}/{settings['weekly_lead_cap']})"

    cur.execute(
        "SELECT COUNT(*) as c FROM handoff_log WHERE started_at >= ? AND status = 'success'",
        (start_of_day.isoformat(),),
    )
    daily_count = cur.fetchone()["c"]
    if daily_count >= settings["daily_lead_cap"]:
        conn.close()
        return False, f"daily cap reached ({daily_count}/{settings['daily_lead_cap']})"

    cur.execute(
        "SELECT started_at FROM handoff_log WHERE status = 'success' "
        "ORDER BY started_at DESC LIMIT 1"
    )
    last_row = cur.fetchone()
    conn.close()

    if last_row:
        last_time = datetime.fromisoformat(last_row["started_at"])
        min_gap = timedelta(minutes=settings["min_interval_minutes"])
        if now - last_time < min_gap:
            wait = min_gap - (now - last_time)
            return False, f"min interval not met, wait {wait}"

    return True, "ok"


def log_result(
    db_path: str,
    lead_id: int,
    session_id: str | None,
    started_at: str,
    duration_ms: int | None,
    cost_usd: float | None,
    status: str,
    error_message: str | None = None,
) -> None:
    """Insert a row into handoff_log after a handoff attempt."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """INSERT INTO handoff_log
           (lead_id, session_id, started_at, duration_ms, cost_usd, status, error_message)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (lead_id, session_id, started_at, duration_ms, cost_usd, status, error_message),
    )
    conn.commit()
    conn.close()
