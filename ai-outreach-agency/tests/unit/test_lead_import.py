import csv
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.lead_import.schema import Lead
from src.lead_import.reader import read_csv
from src.lead_import.db import (
    init_db,
    insert_lead,
    get_all_leads,
    get_lead_by_id,
    normalize_company_name,
    find_duplicate,
)
from src.lead_import.migrations import MIGRATIONS, apply_migrations


# --- Schema tests ---


class TestLeadSchema:
    def test_valid_lead(self):
        lead = Lead(
            company_name="Acme Engineering",
            contact_name="John Smith",
            contact_title="Operations Manager",
            email="john@acme.co.za",
            industry="Manufacturing",
            source="apollo",
        )
        assert lead.company_name == "Acme Engineering"
        assert lead.email == "john@acme.co.za"
        assert lead.status == "new"
        assert lead.region == "Gauteng"

    def test_email_normalized(self):
        lead = Lead(
            company_name="Acme",
            contact_name="John",
            contact_title="Manager",
            email="  JOHN@Acme.CO.ZA  ",
        )
        assert lead.email == "john@acme.co.za"

    def test_missing_company_name_raises(self):
        with pytest.raises(ValueError, match="Missing required field: company_name"):
            Lead(
                company_name="",
                contact_name="John",
                contact_title="Manager",
                email="john@acme.co.za",
            )

    def test_missing_contact_name_raises(self):
        with pytest.raises(ValueError, match="Missing required field: contact_name"):
            Lead(
                company_name="Acme",
                contact_name="  ",
                contact_title="Manager",
                email="john@acme.co.za",
            )

    def test_missing_email_raises(self):
        with pytest.raises(ValueError, match="Missing required field: email"):
            Lead(
                company_name="Acme",
                contact_name="John",
                contact_title="Manager",
                email="",
            )

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            Lead(
                company_name="Acme",
                contact_name="John",
                contact_title="Manager",
                email="not-an-email",
            )

    def test_invalid_source_raises(self):
        with pytest.raises(ValueError, match="Invalid source"):
            Lead(
                company_name="Acme",
                contact_name="John",
                contact_title="Manager",
                email="john@acme.co.za",
                source="twitter",
            )

    def test_employee_count_cast_to_int(self):
        lead = Lead(
            company_name="Acme",
            contact_name="John",
            contact_title="Manager",
            email="john@acme.co.za",
            employee_count="150",
        )
        assert lead.employee_count == 150

    def test_campaign_defaults_to_default(self):
        lead = Lead(
            company_name="Acme",
            contact_name="John",
            contact_title="Manager",
            email="john@acme.co.za",
        )
        assert lead.campaign == "default"


# --- CSV reader tests ---


def _write_csv(path: Path, headers: list, rows: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


class TestCSVReader:
    def test_happy_path(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        _write_csv(
            csv_file,
            ["company_name", "contact_name", "contact_title", "email", "industry", "source"],
            [
                ["Acme Engineering", "John Smith", "Ops Manager", "john@acme.co.za", "Manufacturing", "apollo"],
                ["Beta Fabrication", "Jane Doe", "Procurement", "jane@beta.co.za", "Fabrication", "apollo"],
            ],
        )
        leads = read_csv(csv_file)
        assert len(leads) == 2
        assert leads[0].company_name == "Acme Engineering"
        assert leads[1].email == "jane@beta.co.za"

    def test_alternative_column_names(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        _write_csv(
            csv_file,
            ["Company", "Name", "Title", "Contact Email"],
            [["Acme", "John", "Manager", "john@acme.co.za"]],
        )
        leads = read_csv(csv_file)
        assert len(leads) == 1
        assert leads[0].company_name == "Acme"

    def test_missing_required_field_raises(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        _write_csv(
            csv_file,
            ["company_name", "contact_name", "contact_title", "email"],
            [["Acme", "", "Manager", "john@acme.co.za"]],
        )
        with pytest.raises(ValueError, match="Row 2"):
            read_csv(csv_file)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            read_csv("/nonexistent/leads.csv")

    def test_campaign_column_mapped(self, tmp_path):
        csv_file = tmp_path / "leads.csv"
        _write_csv(
            csv_file,
            ["company_name", "contact_name", "contact_title", "email", "campaign"],
            [["Acme", "John", "Manager", "john@acme.co.za", "gauteng-q3"]],
        )
        leads = read_csv(csv_file)
        assert leads[0].campaign == "gauteng-q3"


# --- Database tests ---


@pytest.fixture
def db_conn(tmp_path):
    conn = init_db(tmp_path / "test.db")
    yield conn
    conn.close()


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
        source="apollo",
    )
    defaults.update(overrides)
    return Lead(**defaults)


class TestDatabase:
    def test_insert_and_retrieve(self, db_conn):
        lead = _make_lead()
        lead_id = insert_lead(db_conn, lead)
        assert lead_id == 1

        retrieved = get_lead_by_id(db_conn, lead_id)
        assert retrieved is not None
        assert retrieved.company_name == "Acme Engineering"
        assert retrieved.email == "john@acme.co.za"
        assert retrieved.id == 1

    def test_get_all_leads(self, db_conn):
        insert_lead(db_conn, _make_lead(email="a@acme.co.za"))
        insert_lead(db_conn, _make_lead(company_name="Beta", email="b@beta.co.za"))
        leads = get_all_leads(db_conn)
        assert len(leads) == 2

    def test_get_nonexistent_lead(self, db_conn):
        assert get_lead_by_id(db_conn, 999) is None

    def test_duplicate_company_email_raises(self, db_conn):
        lead = _make_lead()
        insert_lead(db_conn, lead)
        with pytest.raises(sqlite3.IntegrityError):
            insert_lead(db_conn, lead)

    def test_campaign_persisted_and_retrieved(self, db_conn):
        lead_id = insert_lead(db_conn, _make_lead(campaign="gauteng-q3"))
        retrieved = get_lead_by_id(db_conn, lead_id)
        assert retrieved.campaign == "gauteng-q3"

    def test_campaign_defaults_when_not_specified(self, db_conn):
        lead_id = insert_lead(db_conn, _make_lead())
        retrieved = get_lead_by_id(db_conn, lead_id)
        assert retrieved.campaign == "default"


class TestMigrations:
    def test_fresh_db_has_campaign_column_with_default(self, tmp_path):
        conn = init_db(tmp_path / "fresh.db")
        try:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(leads)")}
            assert "campaign" in columns
        finally:
            conn.close()

    def test_apply_migrations_is_idempotent(self, tmp_path):
        conn = init_db(tmp_path / "fresh.db")
        try:
            apply_migrations(conn)
            apply_migrations(conn)
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            assert version == len(MIGRATIONS)
        finally:
            conn.close()


class TestDeduplication:
    def test_normalize_strips_case_and_whitespace(self):
        assert normalize_company_name("  Acme   Engineering  ") == "acme engineering"

    def test_normalize_strips_legal_suffix(self):
        assert normalize_company_name("ACME ENGINEERING (PTY) LTD") == "acme engineering"
        assert normalize_company_name("Beta Fabrication CC") == "beta fabrication"

    def test_find_duplicate_detects_case_and_suffix_variant(self, db_conn):
        insert_lead(db_conn, _make_lead(company_name="Acme Engineering"))
        variant = _make_lead(company_name="ACME ENGINEERING (PTY) LTD")

        duplicate = find_duplicate(db_conn, variant)

        assert duplicate is not None
        assert duplicate.company_name == "Acme Engineering"

    def test_find_duplicate_returns_none_for_different_company(self, db_conn):
        insert_lead(db_conn, _make_lead(company_name="Acme Engineering"))
        other = _make_lead(company_name="Beta Fabrication", email="john@acme.co.za")

        assert find_duplicate(db_conn, other) is None

    def test_find_duplicate_returns_none_for_different_email(self, db_conn):
        insert_lead(db_conn, _make_lead())
        other = _make_lead(email="different@acme.co.za")

        assert find_duplicate(db_conn, other) is None
