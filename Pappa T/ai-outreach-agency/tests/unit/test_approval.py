import sqlite3

import pytest

from src.lead_import.schema import Lead
from src.asset_gen.schema import AssetResult, AssetType
from src.approval.cli import run_approval_gate
from src.approval.schema import ApprovalResult, Decision
from src.approval.db import init_approvals_table, save_approval


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        id=1,
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
        industry="Manufacturing",
        source="apollo",
    )
    defaults.update(overrides)
    return Lead(**defaults)


def _make_asset(**overrides) -> AssetResult:
    defaults = dict(
        lead_id=1,
        asset_text="# Insight: Acme Engineering\n\nSome insight content.",
        asset_type=AssetType.INSIGHT_DOC,
    )
    defaults.update(overrides)
    return AssetResult(**defaults)


def _fake_input(responses):
    it = iter(responses)
    return lambda _prompt="": next(it)


class TestApprovalGate:
    def test_approve(self):
        lead = _make_lead()
        asset = _make_asset()
        result = run_approval_gate(lead, asset, input_fn=_fake_input(["a"]))

        assert isinstance(result, ApprovalResult)
        assert result.decision == Decision.APPROVED
        assert result.lead_id == 1
        assert result.edited_asset_text is None

    def test_reject(self):
        lead = _make_lead()
        asset = _make_asset()
        result = run_approval_gate(lead, asset, input_fn=_fake_input(["r"]))

        assert result.decision == Decision.REJECTED
        assert result.edited_asset_text is None

    def test_invalid_input_loops_then_approves(self, capsys):
        lead = _make_lead()
        asset = _make_asset()
        result = run_approval_gate(
            lead, asset, input_fn=_fake_input(["x", "123", "a"])
        )

        assert result.decision == Decision.APPROVED
        output = capsys.readouterr().out
        assert "Invalid choice" in output

    def test_quit_raises_system_exit(self):
        lead = _make_lead()
        asset = _make_asset()
        with pytest.raises(SystemExit):
            run_approval_gate(lead, asset, input_fn=_fake_input(["q"]))

    def test_edit_captures_text(self, monkeypatch):
        lead = _make_lead()
        asset = _make_asset()

        edited_content = "# Edited insight\n\nRevised content."
        monkeypatch.setattr(
            "src.approval.cli._edit_asset",
            lambda _text: edited_content,
        )

        result = run_approval_gate(lead, asset, input_fn=_fake_input(["e"]))

        assert result.decision == Decision.EDITED
        assert result.edited_asset_text == edited_content


class TestApprovalDb:
    @pytest.fixture
    def db_conn(self, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.row_factory = sqlite3.Row
        init_approvals_table(conn)
        yield conn
        conn.close()

    def test_save_and_retrieve(self, db_conn):
        result = ApprovalResult(lead_id=1, decision=Decision.APPROVED)
        row_id = save_approval(db_conn, result)

        assert row_id == 1
        row = db_conn.execute(
            "SELECT * FROM approvals WHERE id = ?", (row_id,)
        ).fetchone()
        assert row["lead_id"] == 1
        assert row["decision"] == "approved"
        assert row["edited_asset_text"] is None

    def test_save_edited_approval(self, db_conn):
        result = ApprovalResult(
            lead_id=2,
            decision=Decision.EDITED,
            edited_asset_text="Revised content.",
        )
        row_id = save_approval(db_conn, result)

        row = db_conn.execute(
            "SELECT * FROM approvals WHERE id = ?", (row_id,)
        ).fetchone()
        assert row["decision"] == "edited"
        assert row["edited_asset_text"] == "Revised content."
