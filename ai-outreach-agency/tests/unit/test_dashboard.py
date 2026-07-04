import pytest

from src.lead_import.db import init_db, insert_lead
from src.lead_import.schema import Lead, VALID_STATUSES
from src.approval.db import init_approvals_table, save_approval
from src.approval.schema import ApprovalResult, Decision
from src.dashboard.data import (
    get_status_counts,
    get_campaign_matrix,
    get_approval_history,
    get_summary,
)
from src.dashboard.generator import generate_dashboard_html


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
def db_conn(tmp_path):
    conn = init_db(tmp_path / "test.db")
    yield conn
    conn.close()


def _set_status(conn, lead_id, status):
    conn.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()


class TestGetStatusCounts:
    def test_counts_all_statuses_including_zero(self, db_conn):
        counts = get_status_counts(db_conn)
        assert set(counts.keys()) == VALID_STATUSES
        assert all(v == 0 for v in counts.values())

    def test_counts_reflect_lead_statuses(self, db_conn):
        id1 = insert_lead(db_conn, _make_lead(email="a@acme.co.za"))
        id2 = insert_lead(db_conn, _make_lead(company_name="Beta", email="b@beta.co.za"))
        _set_status(db_conn, id1, "researched")
        _set_status(db_conn, id2, "drafted")

        counts = get_status_counts(db_conn)

        assert counts["researched"] == 1
        assert counts["drafted"] == 1
        assert counts["new"] == 0

    def test_filters_by_campaign(self, db_conn):
        insert_lead(db_conn, _make_lead(email="a@acme.co.za", campaign="gauteng-q3"))
        insert_lead(db_conn, _make_lead(company_name="Beta", email="b@beta.co.za", campaign="referral"))

        counts = get_status_counts(db_conn, campaign="gauteng-q3")

        assert counts["new"] == 1


class TestGetCampaignMatrix:
    def test_groups_by_campaign_and_status(self, db_conn):
        id1 = insert_lead(db_conn, _make_lead(email="a@acme.co.za", campaign="gauteng-q3"))
        insert_lead(db_conn, _make_lead(company_name="Beta", email="b@beta.co.za", campaign="referral"))
        _set_status(db_conn, id1, "approved")

        matrix = get_campaign_matrix(db_conn)

        assert matrix["gauteng-q3"]["approved"] == 1
        assert matrix["gauteng-q3"]["new"] == 0
        assert matrix["referral"]["new"] == 1

    def test_empty_db_returns_empty_matrix(self, db_conn):
        assert get_campaign_matrix(db_conn) == {}


class TestGetApprovalHistory:
    def test_empty_db_returns_empty_list_no_table_error(self, db_conn):
        assert get_approval_history(db_conn) == []

    def test_joins_company_name_and_orders_newest_first(self, db_conn):
        lead_id = insert_lead(db_conn, _make_lead())
        init_approvals_table(db_conn)
        save_approval(
            db_conn,
            ApprovalResult(
                lead_id=lead_id, decision=Decision.APPROVED, decided_at="2026-07-01T10:00:00+00:00"
            ),
        )
        save_approval(
            db_conn,
            ApprovalResult(
                lead_id=lead_id, decision=Decision.REJECTED, decided_at="2026-07-02T10:00:00+00:00"
            ),
        )

        history = get_approval_history(db_conn)

        assert len(history) == 2
        assert history[0]["decision"] == "rejected"
        assert history[0]["company_name"] == "Acme Engineering"
        assert history[1]["decision"] == "approved"

    def test_marks_edited_decisions(self, db_conn):
        lead_id = insert_lead(db_conn, _make_lead())
        init_approvals_table(db_conn)
        save_approval(
            db_conn,
            ApprovalResult(
                lead_id=lead_id,
                decision=Decision.EDITED,
                edited_asset_text="Revised.",
            ),
        )

        history = get_approval_history(db_conn)

        assert history[0]["edited"] is True


class TestGetSummary:
    def test_empty_db_no_divide_by_zero(self, db_conn):
        summary = get_summary(db_conn)
        assert summary["total_leads"] == 0
        assert summary["approval_rate"] == 0.0

    def test_summary_counts_and_rate(self, db_conn):
        id1 = insert_lead(db_conn, _make_lead(email="a@acme.co.za"))
        id2 = insert_lead(db_conn, _make_lead(company_name="Beta", email="b@beta.co.za"))
        id3 = insert_lead(db_conn, _make_lead(company_name="Gamma", email="c@gamma.co.za"))
        _set_status(db_conn, id1, "drafted")
        _set_status(db_conn, id2, "rejected")
        # id3 stays "new"

        summary = get_summary(db_conn)

        assert summary["total_leads"] == 3
        assert summary["drafted"] == 1
        assert summary["rejected"] == 1
        assert summary["approval_rate"] == pytest.approx(0.5)


class TestGenerateDashboardHtml:
    def test_writes_html_file(self, db_conn, tmp_path):
        insert_lead(db_conn, _make_lead())
        output_path = tmp_path / "dashboard.html"

        result = generate_dashboard_html(db_conn, output_path)

        assert result == output_path
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "Acme Engineering" not in content  # funnel view has no per-lead names
        assert "<html" in content.lower()

    def test_creates_missing_parent_dirs(self, db_conn, tmp_path):
        output_path = tmp_path / "nested" / "dir" / "dashboard.html"

        generate_dashboard_html(db_conn, output_path)

        assert output_path.exists()

    def test_includes_status_counts_and_campaign(self, db_conn, tmp_path):
        insert_lead(db_conn, _make_lead(campaign="gauteng-q3"))
        output_path = tmp_path / "dashboard.html"

        generate_dashboard_html(db_conn, output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "gauteng-q3" in content

    def test_includes_approval_history_company_name(self, db_conn, tmp_path):
        lead_id = insert_lead(db_conn, _make_lead())
        init_approvals_table(db_conn)
        save_approval(db_conn, ApprovalResult(lead_id=lead_id, decision=Decision.APPROVED))
        output_path = tmp_path / "dashboard.html"

        generate_dashboard_html(db_conn, output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "Acme Engineering" in content
        assert "approved" in content
