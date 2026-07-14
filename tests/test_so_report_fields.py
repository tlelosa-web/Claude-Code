"""Tests for the Sales Order report-parity fields: SalesOrder.total_incl,
SalesOrder.payment_status (+ its update route), and StockOrder.job_numbers.

See docs/specs/fm-numbers-default-open-so-report.md.
"""
import pytest
from datetime import datetime, timezone
from models import db, SalesOrder, SOLineItem, StockOrder, StockOrderLine, PAYMENT_STATUS_OPTIONS


class TestSalesOrderTotalIncl:
    _c = 0

    def _mk_so(self, session):
        TestSalesOrderTotalIncl._c += 1
        n = TestSalesOrderTotalIncl._c
        so = SalesOrder(so_number=f"REPORT-SO-{n:03d}", customer_name="Report Test Co",
                        status="Draft", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        return so

    def test_total_incl_sums_line_items(self, session):
        so = self._mk_so(session)
        session.add_all([
            SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=1000.0),
            SOLineItem(so_id=so.id, description="Line 2", qty=1.0, incl_total=500.5),
        ])
        session.commit()

        assert so.total_incl == 1500.5

    def test_total_incl_zero_with_no_lines(self, session):
        so = self._mk_so(session)
        session.commit()
        assert so.total_incl == 0

    def test_total_incl_ignores_none_values(self, session):
        so = self._mk_so(session)
        session.add(SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=None))
        session.commit()
        assert so.total_incl == 0


class TestPaymentStatus:
    _c = 0

    def _mk_so(self, session):
        TestPaymentStatus._c += 1
        n = TestPaymentStatus._c
        so = SalesOrder(so_number=f"REPORT-PAY-{n:03d}", customer_name="Report Test Co",
                        status="Draft", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_default_payment_status_is_account_pending(self, session):
        so = self._mk_so(session)
        assert so.payment_status == "Account - Pending"

    def test_update_payment_status_valid(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/payment-status", data={"payment_status": "Cash Sale - Paid"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Cash Sale - Paid"

    def test_update_payment_status_rejects_invalid_value(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/payment-status",
                           data={"payment_status": "Not A Real Status"}, follow_redirects=True)
        assert resp.status_code == 200

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Account - Pending"

    def test_all_options_are_settable(self, client, session):
        so = self._mk_so(session)
        for option in PAYMENT_STATUS_OPTIONS:
            resp = client.post(f"/sales-orders/{so.id}/payment-status", data={"payment_status": option})
            assert resp.status_code == 302
            updated = db.session.get(SalesOrder, so.id)
            assert updated.payment_status == option


class TestStockOrderJobNumbers:
    _c = 0

    def _mk_so(self, session):
        TestStockOrderJobNumbers._c += 1
        n = TestStockOrderJobNumbers._c
        so = SalesOrder(so_number=f"REPORT-STO-{n:03d}", customer_name="Report Test Co",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        return so, n

    def test_job_numbers_rolls_up_distinct_line_values(self, session):
        so, n = self._mk_so(session)
        sto = StockOrder(stock_order_number=f"REPORT-STO-NUM-{n:03d}", so_id=so.id, status="Open",
                         created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.flush()
        session.add_all([
            StockOrderLine(stock_order_id=sto.id, item_code="A1", description="A", qty=1.0, job_number="FM0100"),
            StockOrderLine(stock_order_id=sto.id, item_code="A2", description="B", qty=1.0, job_number="FM0100"),
            StockOrderLine(stock_order_id=sto.id, item_code="A3", description="C", qty=1.0, job_number="FM0101"),
            StockOrderLine(stock_order_id=sto.id, item_code="A4", description="D", qty=1.0, job_number=None),
        ])
        session.commit()

        assert sto.job_numbers == "FM0100, FM0101"

    def test_job_numbers_blank_when_none_set(self, session):
        so, n = self._mk_so(session)
        sto = StockOrder(stock_order_number=f"REPORT-STO-BLANK-{n:03d}", so_id=so.id, status="Open",
                         created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.flush()
        session.add(StockOrderLine(stock_order_id=sto.id, item_code="A1", description="A", qty=1.0))
        session.commit()

        assert sto.job_numbers == ""
