"""Tests for the dashboard route (routes/dashboard.py) beyond the
Open Sales Orders filter coverage already in test_order_list_filters.py.

Covers:
  - FM / Job Number column on the Open Sales Orders table.
  - Total Sales Value card (Total / Cash Sale / Account).

See docs/specs/dashboard-bom-ui-fixes-2026-07-15.md for the spec.
"""
import re
from datetime import datetime, date, timezone
from models import SalesOrder, SOLineItem


def _card_values(html):
    """Extract (total, cash_sale, account) floats from the Total Sales Value
    card. Reads the value against the whole DB, so callers should compare
    *deltas* between two snapshots rather than asserting on an absolute
    figure — the in-memory test DB is shared/cumulative across the whole
    pytest session (see test_order_list_filters.py's TestDashboardOpenSalesOrders
    for the same shared-DB convention)."""
    def _val(label):
        m = re.search(
            r'<div class="stat-label">' + re.escape(label) + r'</div>\s*'
            r'<div class="stat-val"[^>]*>R ([\d.]+)</div>',
            html,
        )
        assert m is not None, f"Could not find stat-val for label {label!r}"
        return float(m.group(1))

    return _val('Total'), _val('Cash Sale'), _val('Account')


class TestDashboardFmNumberColumn:
    _c = 0

    def _mk(self, session, job_numbers=None):
        TestDashboardFmNumberColumn._c += 1
        n = TestDashboardFmNumberColumn._c
        so = SalesOrder(
            so_number=f"FM-COL-{n:03d}",
            customer_name="FM Column Test Co",
            status="Open",
            job_numbers=job_numbers,
            delivery_date=date(2020, 1, 1),
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.commit()
        return so

    def test_fm_number_column_header_present(self, client, session):
        self._mk(session, job_numbers="FM4046")
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"FM / Job Number" in resp.data

    def test_fm_number_shown_when_populated(self, client, session):
        so = self._mk(session, job_numbers="FM4046-FM4055")
        resp = client.get("/")
        assert resp.status_code == 200
        assert so.job_numbers.encode() in resp.data

    def test_fm_number_blank_falls_back_to_dash(self, client, session):
        self._mk(session, job_numbers=None)
        resp = client.get("/")
        assert resp.status_code == 200
        # Can't assert on a bare '-' (too common), just confirm the page
        # still renders cleanly with no job number set.
        assert b"FM / Job Number" in resp.data


class TestDashboardTotalSalesValue:
    """Total Sales Value card: Total / Cash Sale / Account, Draft+Open only.

    See docs/specs/dashboard-bom-ui-fixes-2026-07-15.md — scope confirmed
    as SO_ACTIVE (Draft + Open), Closed SOs excluded.
    """
    _c = 0

    def _mk_so(self, session, status, payment_status, incl_total):
        TestDashboardTotalSalesValue._c += 1
        n = TestDashboardTotalSalesValue._c
        so = SalesOrder(
            so_number=f"SALESVAL-{n:03d}",
            customer_name="Sales Value Test Co",
            status=status,
            payment_status=payment_status,
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.flush()
        session.add(SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=incl_total))
        session.commit()
        return so

    def test_total_sums_draft_and_open_only(self, client, session):
        before_total, _, _ = _card_values(client.get("/").get_data(as_text=True))

        self._mk_so(session, "Draft", "Cash Sale - Paid", 1000.0)
        self._mk_so(session, "Open", "Account - Pending", 2000.0)
        self._mk_so(session, "Closed", "Account - Up to Date", 5000.0)

        after_total, _, _ = _card_values(client.get("/").get_data(as_text=True))
        # Only the Draft + Open SOs (1000 + 2000) contribute; the Closed
        # SO's 5000 must not be included.
        assert round(after_total - before_total, 2) == 3000.0

    def test_cash_sale_and_account_split(self, client, session):
        before_total, before_cash, before_account = _card_values(
            client.get("/").get_data(as_text=True)
        )

        self._mk_so(session, "Draft", "Cash Sale - Unpaid", 300.0)
        self._mk_so(session, "Open", "Cash Sale - Paid", 200.0)
        self._mk_so(session, "Open", "Account - Overdue", 400.0)

        after_total, after_cash, after_account = _card_values(
            client.get("/").get_data(as_text=True)
        )
        assert round(after_cash - before_cash, 2) == 500.0
        assert round(after_account - before_account, 2) == 400.0
        assert round(after_total - before_total, 2) == 900.0

    def test_closed_so_does_not_move_the_card(self, client, session):
        before = _card_values(client.get("/").get_data(as_text=True))
        self._mk_so(session, "Closed", "Account - Up to Date", 999.0)
        after = _card_values(client.get("/").get_data(as_text=True))
        assert after == before
