# HARD RULE: run_approval_gate() is the mandatory human checkpoint.
# The output of run_asset_gen() must pass through this function before
# any email_draft function is called. No code path may bypass this gate.

import os
import subprocess
import sys
import tempfile

from src.lead_import.db import update_lead_status
from src.lead_import.schema import Lead
from src.asset_gen.schema import AssetResult
from .schema import ApprovalResult, Decision

VALID_CHOICES = {"a", "r", "e", "q"}


def _print_review(lead: Lead, asset: AssetResult) -> None:
    print("\n--- LEAD ---")
    print(f"  Company:  {lead.company_name}")
    print(f"  Contact:  {lead.contact_name}")
    print(f"  Title:    {lead.contact_title}")
    print(f"  Email:    {lead.email}")
    print(f"  Industry: {lead.industry or 'N/A'}")
    print(f"  Region:   {lead.region}")
    print("\n--- ASSET ---")
    print(asset.asset_text)
    print("\n--- DECISION ---")
    print("  [A] Approve  [R] Reject  [E] Edit  [Q] Quit")


def _get_choice(input_fn=input) -> str:
    while True:
        choice = input_fn("\n> ").strip().lower()
        if choice in VALID_CHOICES:
            return choice
        print(f"Invalid choice '{choice}'. Enter A, R, E, or Q.")


def _edit_asset(asset_text: str) -> str:
    editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "vi")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(asset_text)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        with open(tmp_path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


def run_approval_gate(
    lead: Lead,
    asset: AssetResult,
    input_fn=input,
    db_path: str | None = None,
) -> ApprovalResult:
    _print_review(lead, asset)
    choice = _get_choice(input_fn=input_fn)

    if choice == "a":
        update_lead_status(lead.id, "approved", db_path)
        return ApprovalResult(lead_id=lead.id, decision=Decision.APPROVED)

    if choice == "r":
        update_lead_status(lead.id, "rejected", db_path)
        return ApprovalResult(lead_id=lead.id, decision=Decision.REJECTED)

    if choice == "e":
        edited_text = _edit_asset(asset.asset_text)
        update_lead_status(lead.id, "approved", db_path)
        return ApprovalResult(
            lead_id=lead.id,
            decision=Decision.EDITED,
            edited_asset_text=edited_text,
        )

    if choice == "q":
        raise SystemExit(0)
