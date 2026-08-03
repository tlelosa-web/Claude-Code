"""
weekly_report.py
Generates docs/reports/handoff-week-<date>.md from handoff_log.

Usage:
    python weekly_report.py --db ai_outreach.db
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def generate_report(db_path: str, settings_path: str = "config/handoff_settings.json") -> Path:
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    now = datetime.now()
    week_start = now - timedelta(days=7)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM handoff_log WHERE started_at >= ? ORDER BY started_at",
        (week_start.isoformat(),),
    )
    rows = cur.fetchall()
    conn.close()

    success_rows = [r for r in rows if r["status"] == "success"]
    throttled_rows = [r for r in rows if r["status"] == "throttled"]
    error_rows = [r for r in rows if r["status"] == "error"]

    total_cost = sum((r["cost_usd"] or 0) for r in success_rows)
    total_duration = sum((r["duration_ms"] or 0) for r in success_rows)
    avg_duration = total_duration / len(success_rows) if success_rows else 0

    quality_counts = {"pass": 0, "edit_heavy": 0, "reject": 0, "unflagged": 0}
    for r in success_rows:
        flag = r["quality_flag"] or "unflagged"
        quality_counts[flag] = quality_counts.get(flag, 0) + 1

    weekly_cap = settings["weekly_lead_cap"]
    cap_usage_pct = (len(success_rows) / weekly_cap * 100) if weekly_cap else 0

    lines = [
        f"# Handoff Weekly Report — {now.strftime('%Y-%m-%d')}",
        "",
        f"**Period:** {week_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
        "",
        "## Volume",
        f"- Leads processed (success): {len(success_rows)} / {weekly_cap} weekly cap "
        f"({cap_usage_pct:.0f}% of cap used)",
        f"- Throttled: {len(throttled_rows)}",
        f"- Errors: {len(error_rows)}",
        "",
        "## Cost & duration",
        f"- Total cost: ${total_cost:.4f} (expected $0.00 under subscription)",
        f"- Total duration: {total_duration} ms",
        f"- Average duration per lead: {avg_duration:.0f} ms",
        "",
        "## Quality",
        f"- Pass: {quality_counts['pass']}",
        f"- Edit-heavy: {quality_counts['edit_heavy']}",
        f"- Reject: {quality_counts['reject']}",
        f"- Unflagged: {quality_counts['unflagged']}",
        "",
    ]

    if throttled_rows or error_rows:
        lines.append("## Issues")
        for r in throttled_rows + error_rows:
            lines.append(
                f"- [{r['status'].upper()}] lead {r['lead_id']} at {r['started_at']}: "
                f"{r['error_message'] or 'no message'}"
            )
        lines.append("")

    lines.append("## Recommendation")
    if cap_usage_pct >= 100:
        lines.append("- Cap reached every run this week. Consider raising weekly_lead_cap.")
    elif cap_usage_pct >= 80:
        lines.append("- Cap usage high (≥80%). Monitor before raising.")
    else:
        lines.append("- Headroom available under current cap.")

    report_dir = Path("docs/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"handoff-week-{now.strftime('%Y-%m-%d')}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to SQLite DB")
    parser.add_argument(
        "--settings", default="config/handoff_settings.json", help="Path to settings JSON"
    )
    args = parser.parse_args()

    path = generate_report(args.db, args.settings)
    print(f"Report written to {path}")
