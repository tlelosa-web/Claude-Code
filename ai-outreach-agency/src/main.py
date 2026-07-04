import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import load_settings
from src.lead_import.reader import read_csv
from src.lead_import.db import (
    init_db,
    insert_lead,
    find_duplicate,
    get_all_leads,
    get_leads_by_status,
    get_lead_by_id,
)
from src.research.pipeline import research_lead
from src.asset_gen.pipeline import run_asset_gen
from src.asset_gen.schema import AssetType
from src.approval.cli import run_approval_gate
from src.approval.schema import Decision
from src.email_draft.pipeline import run_email_draft


def _get_db(settings) -> sqlite3.Connection:
    return init_db(Path(settings.DB_PATH))


def _log_session(message: str) -> None:
    log_path = Path(__file__).parent.parent / "docs" / "session-log.md"
    if not log_path.exists():
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n- [{timestamp}] {message}")


def cmd_import(args, settings) -> None:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)

    leads = read_csv(csv_path)
    conn = _get_db(settings)

    imported = 0
    skipped = 0
    for lead in leads:
        if find_duplicate(conn, lead) is not None:
            skipped += 1
            continue
        try:
            insert_lead(conn, lead)
            imported += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.close()
    print(f"Import complete: {imported} leads imported, {skipped} skipped as duplicates.")
    _log_session(f"Imported {imported} leads from {csv_path.name} ({skipped} duplicates skipped)")


def cmd_list(args, settings) -> None:
    conn = _get_db(settings)
    status = getattr(args, "status", None)

    if status:
        leads = get_leads_by_status(conn, status)
    else:
        leads = get_all_leads(conn)

    conn.close()

    if not leads:
        print("No leads found.")
        return

    print(f"{'ID':<6} {'Company':<30} {'Contact':<25} {'Status':<12}")
    print("-" * 73)
    for lead in leads:
        print(f"{lead.id:<6} {lead.company_name:<30} {lead.contact_name:<25} {lead.status:<12}")

    print(f"\nTotal: {len(leads)} leads")


def _run_single_lead(lead, settings) -> None:
    db_path = str(Path(settings.DB_PATH))
    print(f"\n=== Processing: {lead.company_name} (ID {lead.id}) ===")

    print("\n[1/4] Research...")
    research = research_lead(lead, db_path=db_path)
    print(f"  Summary: {research.summary[:80]}...")

    asset_type_str = settings.DEFAULT_ASSET_TYPE
    asset_type = AssetType[asset_type_str]

    print("\n[2/4] Asset generation...")
    asset = run_asset_gen(lead, research, asset_type=asset_type, db_path=db_path)
    print(f"  Generated {asset.asset_type.value} ({len(asset.asset_text)} chars)")

    print("\n[3/4] Approval gate...")
    approval = run_approval_gate(lead, asset, db_path=db_path)

    if approval.decision == Decision.REJECTED:
        print("  REJECTED — skipping email draft.")
        _log_session(f"Lead {lead.id} ({lead.company_name}): rejected at approval")
        return

    print(f"  Decision: {approval.decision.value}")

    print("\n[4/4] Email draft...")
    draft = run_email_draft(lead, approval, asset, db_path=db_path)
    print(f"  Draft created: {draft.gmail_draft_id}")
    print(f"  Subject: {draft.subject}")

    _log_session(
        f"Lead {lead.id} ({lead.company_name}): "
        f"pipeline complete, draft {draft.gmail_draft_id}"
    )


def cmd_run(args, settings) -> None:
    conn = _get_db(settings)
    lead = get_lead_by_id(conn, args.lead_id)
    conn.close()

    if lead is None:
        print(f"Error: no lead found with ID {args.lead_id}")
        sys.exit(1)

    _run_single_lead(lead, settings)


def cmd_run_all(args, settings) -> None:
    status = args.status or "new"
    conn = _get_db(settings)
    leads = get_leads_by_status(conn, status)
    conn.close()

    if not leads:
        print(f"No leads with status '{status}'.")
        return

    print(f"Found {len(leads)} leads with status '{status}'. Processing one at a time.\n")
    _log_session(f"Starting run-all for {len(leads)} leads with status '{status}'")

    for lead in leads:
        try:
            _run_single_lead(lead, settings)
        except SystemExit:
            print("\nQuit requested. Stopping pipeline.")
            break


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-outreach",
        description="AI Outreach Agency — B2B pipeline CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_import = subparsers.add_parser("import", help="Import leads from CSV")
    p_import.add_argument("--csv", required=True, help="Path to CSV file")

    p_list = subparsers.add_parser("list", help="List leads")
    p_list.add_argument("--status", default=None, help="Filter by status")

    p_run = subparsers.add_parser("run", help="Run pipeline for a single lead")
    p_run.add_argument("--lead-id", type=int, required=True, help="Lead ID to process")

    p_run_all = subparsers.add_parser("run-all", help="Run pipeline for all leads with status")
    p_run_all.add_argument("--status", default="new", help="Status to filter by (default: new)")

    return parser


def main(argv=None) -> None:
    settings = load_settings()
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "import": cmd_import,
        "list": cmd_list,
        "run": cmd_run,
        "run-all": cmd_run_all,
    }

    dispatch[args.command](args, settings)


if __name__ == "__main__":
    main()
