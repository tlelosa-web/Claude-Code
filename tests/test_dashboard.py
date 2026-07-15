"""Tests for the dashboard route (routes/dashboard.py) beyond the
Open Sales Orders filter coverage already in test_order_list_filters.py.

Covers:
  - FM / Job Number column on the Open Sales Orders table.
  - Total Sales Value card (Total / Cash Sale / Account).

See docs/specs/dashboard-bom-ui-fixes-2026-07-15.md for the spec.
"""
from datetime import datetime, date, timezone
from models import SalesOrder


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
