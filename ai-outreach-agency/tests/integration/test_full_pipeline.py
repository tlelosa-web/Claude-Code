"""End-to-end integration tests for the outreach pipeline in OFFLINE_MODE.

All stages run against a real temp SQLite DB with stubs — no API calls.
"""

import csv
import sqlite3

import pytest

from src.lead_import.reader import read_csv
from src.lead_import.schema import Lead
from src.lead_import.db import (
    init_db,
    insert_lead,
    get_all_leads,
    get_lead_by_id,
)
from src.research.pipeline import research_lead
from src.asset_gen.pipeline import run_asset_gen
from src.asset_gen.schema import AssetType
from src.approval.cli import run_approval_gate
from src.approval.schema import Decision
from src.email_draft.pipeline import run_email_draft
from src.email_draft.schema import DraftResult
from src.main import main


# ── fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def offline_mode(monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "true")


@pytest.fixture
def db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_leads.db"
    monkeypatch.setattr("src.lead_import.db.DEFAULT_DB_PATH", db_path)
    conn = init_db(db_path)
    yield conn, str(db_path)
    conn.close()


@pytest.fixture
def sample_csv(tmp_path):
    csv_path = tmp_path / "leads.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Company", "Name", "Title", "Email",
            "Phone", "Website", "Industry",
        ])
        writer.writerow([
            "Acme Engineering", "John Smith", "Operations Manager",
            "john@acme.co.za", "011-555-0001",
            "https://acme.co.za", "Manufacturing",
        ])
        writer.writerow([
            "Bolt Fabrication", "Jane Doe", "Engineering Manager",
            "jane@bolt.co.za", "011-555-0002",
            "https://bolt.co.za", "Fabrication",
        ])
    return csv_path


def _import_csv(csv_path, conn):
    """Import leads from CSV into the DB, return (imported, skipped)."""
    leads = read_csv(csv_path)
    imported = 0
    skipped = 0
    for lead in leads:
        try:
            insert_lead(conn, lead)
            imported += 1
        except sqlite3.IntegrityError:
            skipped += 1
    return imported, skipped


def _run_pipeline(lead, db_path, approval_input):
    """Run research → asset_gen → approval → email_draft for one lead."""
    research = research_lead(lead, db_path=db_path)
    asset = run_asset_gen(lead, research, asset_type=AssetType.INSIGHT_DOC, db_path=db_path)
    approval = run_approval_gate(
        lead, asset,
        input_fn=lambda _prompt: approval_input,
        db_path=db_path,
    )
    if approval.decision == Decision.REJECTED:
        return approval, None
    draft = run_email_draft(lead, approval, asset, db_path=db_path)
    return approval, draft


# ── tests ─────────────────────────────────────────────────────────────


class TestHappyPath:
    def test_csv_to_draft(self, db, sample_csv):
        conn, db_path = db
        imported, skipped = _import_csv(sample_csv, conn)
        assert imported == 2
        assert skipped == 0

        leads = get_all_leads(conn)
        assert len(leads) == 2

        for lead in leads:
            lead_db = get_lead_by_id(conn, lead.id)
            assert lead_db.status == "new"

            approval, draft = _run_pipeline(lead_db, db_path, "a")

            assert approval.decision == Decision.APPROVED
            assert isinstance(draft, DraftResult)
            assert draft.lead_id == lead.id
            assert draft.gmail_draft_id.startswith("draft_")
            assert draft.subject.startswith("A quick insight for")

            final = get_lead_by_id(conn, lead.id)
            assert final.status == "drafted"


class TestRejectionPath:
    def test_reject_creates_no_draft(self, db, sample_csv):
        conn, db_path = db
        _import_csv(sample_csv, conn)

        lead = get_all_leads(conn)[0]
        approval, draft = _run_pipeline(lead, db_path, "r")

        assert approval.decision == Decision.REJECTED
        assert draft is None

        final = get_lead_by_id(conn, lead.id)
        assert final.status == "rejected"


class TestMainCLIRunCommand:
    """Regression test: main.py's _run_single_lead must thread settings.DB_PATH
    into every pipeline stage. Prior to this test, it silently fell back to
    lead_import.db.DEFAULT_DB_PATH (a different file with no schema), which
    crashed on the first status update outside of unit tests (which mock
    update_lead_status and never exercise the real DB write)."""

    def test_run_writes_status_to_settings_db_path(
        self, tmp_path, monkeypatch, sample_csv
    ):
        import io

        db_path = tmp_path / "cli_test.db"
        monkeypatch.setenv("DB_PATH", str(db_path))
        monkeypatch.setenv("OFFLINE_MODE", "true")
        monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))

        init_db(db_path).close()
        main(["import", "--csv", str(sample_csv)])

        conn = init_db(db_path)
        lead_id = get_all_leads(conn)[0].id
        conn.close()

        main(["run", "--lead-id", str(lead_id)])

        conn = init_db(db_path)
        final = get_lead_by_id(conn, lead_id)
        conn.close()

        assert final.status == "drafted"

    def test_run_asset_type_override_reaches_asset_gen(
        self, tmp_path, monkeypatch, sample_csv, capsys
    ):
        import io

        db_path = tmp_path / "cli_test.db"
        monkeypatch.setenv("DB_PATH", str(db_path))
        monkeypatch.setenv("OFFLINE_MODE", "true")
        monkeypatch.setattr("sys.stdin", io.StringIO("a\n"))

        init_db(db_path).close()
        main(["import", "--csv", str(sample_csv)])

        conn = init_db(db_path)
        lead_id = get_all_leads(conn)[0].id
        conn.close()

        main(["run", "--lead-id", str(lead_id), "--asset-type", "PAIN_POINT_SUMMARY"])

        output = capsys.readouterr().out
        assert "pain_point_summary" in output

    def test_run_all_filters_by_campaign(self, tmp_path, monkeypatch, sample_csv, capsys):
        import io

        db_path = tmp_path / "cli_test.db"
        monkeypatch.setenv("DB_PATH", str(db_path))
        monkeypatch.setenv("OFFLINE_MODE", "true")
        monkeypatch.setattr("sys.stdin", io.StringIO("a\na\n"))

        init_db(db_path).close()
        main(["import", "--csv", str(sample_csv), "--campaign", "gauteng-q3"])

        conn = init_db(db_path)
        insert_lead(
            conn,
            Lead(
                company_name="Other Co",
                contact_name="Sam",
                contact_title="Manager",
                email="sam@other.co.za",
                campaign="referral",
            ),
        )
        conn.close()

        main(["run-all", "--campaign", "gauteng-q3"])

        output = capsys.readouterr().out
        assert "Found 2 leads" in output
        assert "Other Co" not in output


class TestDuplicateImport:
    def test_second_import_skips_duplicates(self, db, sample_csv):
        conn, db_path = db
        imported_1, skipped_1 = _import_csv(sample_csv, conn)
        assert imported_1 == 2
        assert skipped_1 == 0

        imported_2, skipped_2 = _import_csv(sample_csv, conn)
        assert imported_2 == 0
        assert skipped_2 == 2

        all_leads = get_all_leads(conn)
        assert len(all_leads) == 2
