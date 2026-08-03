import sqlite3
from pathlib import Path

import pytest

from src.lead_import.schema import Lead
from src.lead_import.db import init_db, insert_lead, update_lead_status, get_lead_by_id


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


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    lead = _make_lead()
    lead_id = insert_lead(conn, lead)
    conn.close()
    return db_path, lead_id


class TestStatusTransitions:
    def test_new_to_researched(self, db):
        db_path, lead_id = db
        update_lead_status(lead_id, "researched", str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        assert row["status"] == "researched"

    def test_researched_to_asset_ready(self, db):
        db_path, lead_id = db
        update_lead_status(lead_id, "researched", str(db_path))
        update_lead_status(lead_id, "asset_ready", str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        assert row["status"] == "asset_ready"

    def test_asset_ready_to_approved(self, db):
        db_path, lead_id = db
        update_lead_status(lead_id, "researched", str(db_path))
        update_lead_status(lead_id, "asset_ready", str(db_path))
        update_lead_status(lead_id, "approved", str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        assert row["status"] == "approved"

    def test_approved_to_drafted(self, db):
        db_path, lead_id = db
        update_lead_status(lead_id, "researched", str(db_path))
        update_lead_status(lead_id, "asset_ready", str(db_path))
        update_lead_status(lead_id, "approved", str(db_path))
        update_lead_status(lead_id, "drafted", str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        assert row["status"] == "drafted"

    def test_asset_ready_to_rejected(self, db):
        db_path, lead_id = db
        update_lead_status(lead_id, "researched", str(db_path))
        update_lead_status(lead_id, "asset_ready", str(db_path))
        update_lead_status(lead_id, "rejected", str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        assert row["status"] == "rejected"


class TestHappyPath:
    def test_full_lifecycle(self, db):
        db_path, lead_id = db
        for status in ["researched", "asset_ready", "approved", "drafted"]:
            update_lead_status(lead_id, status, str(db_path))
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        assert row["status"] == "drafted"


class TestRejectedLeadStaysRejected:
    def test_rejected_cannot_transition(self, db):
        db_path, lead_id = db
        update_lead_status(lead_id, "researched", str(db_path))
        update_lead_status(lead_id, "asset_ready", str(db_path))
        update_lead_status(lead_id, "rejected", str(db_path))
        with pytest.raises(ValueError, match="Invalid transition"):
            update_lead_status(lead_id, "approved", str(db_path))


class TestInvalidTransitions:
    def test_new_to_approved_raises(self, db):
        db_path, lead_id = db
        with pytest.raises(ValueError, match="Invalid transition"):
            update_lead_status(lead_id, "approved", str(db_path))

    def test_new_to_drafted_raises(self, db):
        db_path, lead_id = db
        with pytest.raises(ValueError, match="Invalid transition"):
            update_lead_status(lead_id, "drafted", str(db_path))

    def test_nonexistent_lead_raises(self, db):
        db_path, _ = db
        with pytest.raises(ValueError, match="not found"):
            update_lead_status(999, "researched", str(db_path))
