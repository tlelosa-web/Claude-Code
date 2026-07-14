"""Tests for the '?view=open|all' filter on the 4 list_orders() routes
(Sales Orders, Works Orders, Stock Orders, Purchase Orders) and for the
Dashboard's Open Sales Orders table.

See docs/specs/dashboard-open-filter.md for the active-status decisions:
  SO:  Draft, Open        (excludes Closed)
  WO:  Open, In Progress  (excludes Complete, Cancelled)
  STO: Open               (excludes Complete, Cancelled)
  PO:  Draft, Open, Partially Received (excludes Received, Cancelled)

Default view is 'open' (flipped from 'all' in
docs/specs/fm-numbers-default-open-so-report.md, 2026-07-10) — the bare
list URL now shows only active/open records; '?view=all' is the explicit
opt-in to see everything.

Uses distinct 'FILT-*' number prefixes to avoid colliding with
auto-generated numbers from other test modules sharing the same
session-scoped in-memory DB (established convention, see
test_stock_orders.py).
"""
from datetime import datetime, date, timezone
from models import SalesOrder, WorksOrder, StockOrder, PurchaseOrder


class TestSalesOrderListFilter:
    _c = 0

    def _mk(self, session, status):
        TestSalesOrderListFilter._c += 1
        n = TestSalesOrderListFilter._c
        so = SalesOrder(
            so_number=f"FILT-SO-{n:03d}",
            customer_name="Filter Test Co",
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.commit()
        return so

    def test_default_view_hides_closed(self, client, session):
        open_so = self._mk(session, "Open")
        closed_so = self._mk(session, "Closed")
        resp = client.get("/sales-orders")
        assert resp.status_code == 200
        assert open_so.so_number.encode() in resp.data
        assert closed_so.so_number.encode() not in resp.data

    def test_all_view_shows_all_statuses(self, client, session):
        open_so = self._mk(session, "Open")
        closed_so = self._mk(session, "Closed")
        resp = client.get("/sales-orders?view=all")
        assert resp.status_code == 200
        assert open_so.so_number.encode() in resp.data
        assert closed_so.so_number.encode() in resp.data

    def test_open_view_hides_closed(self, client, session):
        open_so = self._mk(session, "Open")
        draft_so = self._mk(session, "Draft")
        closed_so = self._mk(session, "Closed")
        resp = client.get("/sales-orders?view=open")
        assert resp.status_code == 200
        assert open_so.so_number.encode() in resp.data
        assert draft_so.so_number.encode() in resp.data
        assert closed_so.so_number.encode() not in resp.data

    def test_closed_view_shows_only_closed(self, client, session):
        open_so = self._mk(session, "Open")
        draft_so = self._mk(session, "Draft")
        closed_so = self._mk(session, "Closed")
        resp = client.get("/sales-orders?view=closed")
        assert resp.status_code == 200
        assert open_so.so_number.encode() not in resp.data
        assert draft_so.so_number.encode() not in resp.data
        assert closed_so.so_number.encode() in resp.data


class TestWorksOrderListFilter:
    _c = 0

    def _mk(self, session, status):
        TestWorksOrderListFilter._c += 1
        n = TestWorksOrderListFilter._c
        so = SalesOrder(so_number=f"FILT-WOSO-{n:03d}", customer_name="Filter Test Co",
                         status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        wo = WorksOrder(wo_number=f"FILT-WO-{n:03d}", so_id=so.id, order_type="ASSEMBLY",
                         status=status, issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.commit()
        return wo

    def test_default_view_hides_complete(self, client, session):
        open_wo = self._mk(session, "Open")
        complete_wo = self._mk(session, "Complete")
        resp = client.get("/works-orders")
        assert resp.status_code == 200
        assert open_wo.wo_number.encode() in resp.data
        assert complete_wo.wo_number.encode() not in resp.data

    def test_all_view_shows_all_statuses(self, client, session):
        open_wo = self._mk(session, "Open")
        complete_wo = self._mk(session, "Complete")
        resp = client.get("/works-orders?view=all")
        assert resp.status_code == 200
        assert open_wo.wo_number.encode() in resp.data
        assert complete_wo.wo_number.encode() in resp.data

    def test_open_view_hides_complete_and_cancelled(self, client, session):
        open_wo = self._mk(session, "Open")
        in_progress_wo = self._mk(session, "In Progress")
        complete_wo = self._mk(session, "Complete")
        cancelled_wo = self._mk(session, "Cancelled")
        resp = client.get("/works-orders?view=open")
        assert resp.status_code == 200
        assert open_wo.wo_number.encode() in resp.data
        assert in_progress_wo.wo_number.encode() in resp.data
        assert complete_wo.wo_number.encode() not in resp.data
        assert cancelled_wo.wo_number.encode() not in resp.data

    def test_closed_view_shows_complete_and_cancelled(self, client, session):
        open_wo = self._mk(session, "Open")
        in_progress_wo = self._mk(session, "In Progress")
        complete_wo = self._mk(session, "Complete")
        cancelled_wo = self._mk(session, "Cancelled")
        resp = client.get("/works-orders?view=closed")
        assert resp.status_code == 200
        assert open_wo.wo_number.encode() not in resp.data
        assert in_progress_wo.wo_number.encode() not in resp.data
        assert complete_wo.wo_number.encode() in resp.data
        assert cancelled_wo.wo_number.encode() in resp.data


class TestStockOrderListFilter:
    _c = 0

    def _mk(self, session, status):
        TestStockOrderListFilter._c += 1
        n = TestStockOrderListFilter._c
        so = SalesOrder(so_number=f"FILT-STOSO-{n:03d}", customer_name="Filter Test Co",
                         status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        sto = StockOrder(stock_order_number=f"FILT-STO-{n:03d}", so_id=so.id, status=status,
                          created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.commit()
        return sto

    def test_default_view_hides_complete_and_cancelled(self, client, session):
        open_sto = self._mk(session, "Open")
        complete_sto = self._mk(session, "Complete")
        resp = client.get("/stock-orders")
        assert resp.status_code == 200
        assert open_sto.stock_order_number.encode() in resp.data
        assert complete_sto.stock_order_number.encode() not in resp.data

    def test_all_view_shows_all_statuses(self, client, session):
        open_sto = self._mk(session, "Open")
        complete_sto = self._mk(session, "Complete")
        resp = client.get("/stock-orders?view=all")
        assert resp.status_code == 200
        assert open_sto.stock_order_number.encode() in resp.data
        assert complete_sto.stock_order_number.encode() in resp.data

    def test_open_view_hides_complete_and_cancelled(self, client, session):
        open_sto = self._mk(session, "Open")
        complete_sto = self._mk(session, "Complete")
        cancelled_sto = self._mk(session, "Cancelled")
        resp = client.get("/stock-orders?view=open")
        assert resp.status_code == 200
        assert open_sto.stock_order_number.encode() in resp.data
        assert complete_sto.stock_order_number.encode() not in resp.data
        assert cancelled_sto.stock_order_number.encode() not in resp.data

    def test_closed_view_shows_complete_and_cancelled(self, client, session):
        open_sto = self._mk(session, "Open")
        complete_sto = self._mk(session, "Complete")
        cancelled_sto = self._mk(session, "Cancelled")
        resp = client.get("/stock-orders?view=closed")
        assert resp.status_code == 200
        assert open_sto.stock_order_number.encode() not in resp.data
        assert complete_sto.stock_order_number.encode() in resp.data
        assert cancelled_sto.stock_order_number.encode() in resp.data

    def test_open_view_includes_picking_closed_view_excludes_it(self, client, session):
        """A Picking STO is still in-progress — it belongs in the 'Open' list view
        alongside Open orders, not in 'Closed'."""
        picking_sto = self._mk(session, "Picking")

        resp = client.get("/stock-orders?view=open")
        assert resp.status_code == 200
        assert picking_sto.stock_order_number.encode() in resp.data

        resp = client.get("/stock-orders?view=closed")
        assert resp.status_code == 200
        assert picking_sto.stock_order_number.encode() not in resp.data


class TestPurchaseOrderListFilter:
    _c = 0

    def _mk(self, session, status):
        TestPurchaseOrderListFilter._c += 1
        n = TestPurchaseOrderListFilter._c
        po = PurchaseOrder(po_number=f"FILT-PO-{n:03d}", supplier_name="Filter Supplier",
                            status=status, created_at=datetime.now(timezone.utc))
        session.add(po)
        session.commit()
        return po

    def test_default_view_hides_received_and_cancelled(self, client, session):
        open_po = self._mk(session, "Open")
        received_po = self._mk(session, "Received")
        resp = client.get("/purchase-orders")
        assert resp.status_code == 200
        assert open_po.po_number.encode() in resp.data
        assert received_po.po_number.encode() not in resp.data

    def test_all_view_shows_all_statuses(self, client, session):
        open_po = self._mk(session, "Open")
        received_po = self._mk(session, "Received")
        resp = client.get("/purchase-orders?view=all")
        assert resp.status_code == 200
        assert open_po.po_number.encode() in resp.data
        assert received_po.po_number.encode() in resp.data

    def test_open_view_hides_received_and_cancelled(self, client, session):
        draft_po = self._mk(session, "Draft")
        open_po = self._mk(session, "Open")
        partial_po = self._mk(session, "Partially Received")
        received_po = self._mk(session, "Received")
        cancelled_po = self._mk(session, "Cancelled")
        resp = client.get("/purchase-orders?view=open")
        assert resp.status_code == 200
        assert draft_po.po_number.encode() in resp.data
        assert open_po.po_number.encode() in resp.data
        assert partial_po.po_number.encode() in resp.data
        assert received_po.po_number.encode() not in resp.data
        assert cancelled_po.po_number.encode() not in resp.data


class TestDashboardOpenSalesOrders:
    _c = 0

    def _mk(self, session, status):
        TestDashboardOpenSalesOrders._c += 1
        n = TestDashboardOpenSalesOrders._c
        # Explicit early delivery_date guarantees these sort first (ascending,
        # nulls last) ahead of the many null-delivery-date SOs other test
        # modules leave behind in the shared session-scoped in-memory DB -
        # otherwise the dashboard's .limit(10) could push these out of view
        # depending on test execution order/count.
        so = SalesOrder(so_number=f"FILT-DASH-{n:03d}", customer_name="Filter Test Co",
                         status=status, delivery_date=date(2020, 1, 1),
                         created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_dashboard_shows_open_hides_closed(self, client, session):
        open_so = self._mk(session, "Open")
        draft_so = self._mk(session, "Draft")
        closed_so = self._mk(session, "Closed")
        resp = client.get("/")
        assert resp.status_code == 200
        assert open_so.so_number.encode() in resp.data
        assert draft_so.so_number.encode() in resp.data
        assert closed_so.so_number.encode() not in resp.data
