import sqlite3
from pathlib import Path
from typing import Optional

from src.lead_import.schema import VALID_STATUSES
from .data import get_approval_history, get_campaign_matrix, get_status_counts, get_summary

_STATUS_ORDER = ["new", "researched", "asset_ready", "approved", "rejected", "drafted", "sent"]
_STATUS_COLUMNS = [s for s in _STATUS_ORDER if s in VALID_STATUSES]

# Funnel bar colors: gray = not started, violet = in progress, green/red = terminal outcome.
_STATUS_COLORS = {
    "new": "var(--muted)",
    "researched": "var(--accent)",
    "asset_ready": "var(--accent)",
    "approved": "var(--good)",
    "rejected": "var(--critical)",
    "drafted": "var(--good)",
    "sent": "var(--good)",
}

# Tinted badges (light bg + dark-enough text) for the approval decision column.
_DECISION_PILLS = {
    "approved": ("#ECFDF5", "#047857"),
    "rejected": ("#FEF2F2", "#B91C1C"),
    "edited": ("#FFFBEB", "#92400E"),
}

_STYLE = """
:root {
  --page-bg: #F4F5FA;
  --surface: #FFFFFF;
  --ink: #1B1B1F;
  --ink-secondary: #6B7280;
  --muted: #9CA3AF;
  --accent: #4a3aa7;
  --accent-soft: #EDEAFB;
  --good: #0ca30c;
  --critical: #d03b3b;
  --border: rgba(11,11,11,0.08);
}
* { box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  margin: 0;
  background: var(--page-bg);
  color: var(--ink);
}
.app { display: flex; min-height: 100vh; }
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 1.5rem 1rem;
}
.brand { font-weight: 700; font-size: 1.1rem; margin-bottom: 1.5rem; padding: 0 0.5rem; }
.nav-item {
  display: block;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  color: var(--ink-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}
.nav-item:hover { background: var(--accent-soft); color: var(--accent); }
.nav-item.active { background: var(--accent); color: #fff; }
.content { flex: 1; padding: 2rem 2.5rem; max-width: 1100px; }
.topbar { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 1.5rem; }
.topbar h1 { font-size: 1.4rem; margin: 0; }
.topbar .subtitle { color: var(--ink-secondary); font-size: 0.9rem; margin: 0.15rem 0 0; }
.cards { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.4rem;
  min-width: 150px;
  flex: 1;
}
.card .icon {
  width: 36px; height: 36px; border-radius: 50%;
  background: var(--accent-soft); color: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; margin-bottom: 0.6rem;
}
.card .value { font-size: 1.6rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.card .label { color: var(--ink-secondary); font-size: 0.8rem; margin-top: 0.15rem; }
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
  scroll-margin-top: 1rem;
}
.panel h2 { font-size: 1rem; margin: 0 0 1rem; }
.bar-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.65rem; font-size: 0.85rem; }
.bar-row .bar-label { width: 100px; flex-shrink: 0; color: var(--ink-secondary); }
.bar-row .bar-track { flex: 1; background: var(--page-bg); border-radius: 6px; height: 18px; overflow: hidden; }
.bar-row .bar-fill { height: 100%; border-radius: 6px; min-width: 3px; }
.bar-row .bar-count { width: 32px; text-align: right; font-variant-numeric: tabular-nums; flex-shrink: 0; }
table { border-collapse: collapse; width: 100%; }
th, td { padding: 0.55rem 0.75rem; text-align: left; font-size: 0.85rem; border-bottom: 1px solid var(--border); }
th { color: var(--ink-secondary); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.02em; }
tr:last-child td { border-bottom: none; }
tbody tr:hover { background: var(--page-bg); }
.pill { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; text-transform: capitalize; }
.empty { color: var(--ink-secondary); font-size: 0.85rem; }
"""


def _summary_cards_html(summary: dict) -> str:
    cards = [
        ("\U0001f465", "Total Leads", summary["total_leads"]),
        ("✓", "Approved", summary["approved"]),
        ("✕", "Rejected", summary["rejected"]),
        ("✉", "Drafted", summary["drafted"]),
        ("\U0001f4c8", "Approval Rate", f"{summary['approval_rate']:.0%}"),
    ]
    items = "".join(
        f'<div class="card"><div class="icon">{icon}</div>'
        f'<div class="value">{value}</div><div class="label">{label}</div></div>'
        for icon, label, value in cards
    )
    return f'<div class="cards">{items}</div>'


def _funnel_bars_html(counts: dict[str, int]) -> str:
    max_count = max(counts.values(), default=0) or 1
    rows = ""
    for status in _STATUS_COLUMNS:
        count = counts.get(status, 0)
        width = max(3, round(count / max_count * 100)) if count else 0
        color = _STATUS_COLORS.get(status, "var(--accent)")
        rows += (
            '<div class="bar-row">'
            f'<div class="bar-label">{status}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;background:{color};"></div></div>'
            f'<div class="bar-count">{count}</div>'
            "</div>"
        )
    return rows


def _campaign_matrix_html(matrix: dict[str, dict[str, int]]) -> str:
    if not matrix:
        return '<p class="empty">No campaigns yet.</p>'
    header = "<th>Campaign</th>" + "".join(f"<th>{status}</th>" for status in _STATUS_COLUMNS)
    rows = ""
    for campaign in sorted(matrix):
        counts = matrix[campaign]
        cells = "".join(f"<td>{counts.get(status, 0)}</td>" for status in _STATUS_COLUMNS)
        rows += f"<tr><td>{campaign}</td>{cells}</tr>"
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"


def _decision_pill_html(decision: str) -> str:
    bg, text = _DECISION_PILLS.get(decision, ("#F3F4F6", "#374151"))
    return f'<span class="pill" style="background:{bg};color:{text};">{decision}</span>'


def _approval_history_html(history: list[dict]) -> str:
    if not history:
        return '<p class="empty">No approval decisions recorded yet.</p>'
    rows = "".join(
        f"<tr><td>{entry['company_name']}</td><td>{_decision_pill_html(entry['decision'])}</td>"
        f"<td>{'Yes' if entry['edited'] else 'No'}</td><td>{entry['decided_at']}</td></tr>"
        for entry in history
    )
    return (
        "<table><thead><tr><th>Company</th><th>Decision</th><th>Edited</th>"
        f"<th>Decided At</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def generate_dashboard_html(
    conn: sqlite3.Connection,
    output_path: str | Path,
    owner_name: Optional[str] = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = get_summary(conn)
    counts = get_status_counts(conn)
    matrix = get_campaign_matrix(conn)
    history = get_approval_history(conn)
    greeting = f"Hello {owner_name} \U0001f44b" if owner_name else "Dashboard"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>AI Outreach Dashboard</title>
<style>{_STYLE}</style>
</head>
<body>
<div class="app">
<nav class="sidebar">
  <div class="brand">AI Outreach</div>
  <a class="nav-item active" href="#overview">Dashboard</a>
  <a class="nav-item" href="#funnel">Pipeline</a>
  <a class="nav-item" href="#campaigns">Campaigns</a>
  <a class="nav-item" href="#approvals">Approvals</a>
</nav>
<main class="content" id="overview">
  <div class="topbar">
    <div>
      <h1>{greeting}</h1>
      <p class="subtitle">Lead pipeline overview</p>
    </div>
  </div>
  {_summary_cards_html(summary)}
  <section class="panel" id="funnel">
    <h2>Pipeline Funnel</h2>
    {_funnel_bars_html(counts)}
  </section>
  <section class="panel" id="campaigns">
    <h2>Campaigns</h2>
    {_campaign_matrix_html(matrix)}
  </section>
  <section class="panel" id="approvals">
    <h2>Approval History</h2>
    {_approval_history_html(history)}
  </section>
</main>
</div>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path
