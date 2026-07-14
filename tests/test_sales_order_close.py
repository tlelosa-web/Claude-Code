"""Tests for Sales Order closing — manual /close route and auto-close on
WO/STO completion via can_close_sales_order()."""
import pytest
from datetime import datetime, timezone
from models import db, SalesOrder, WorksOrder, StockOrder, StockOrderLine, BOMLine, Item


class TestSalesOrderClose:
    _so_counter = 0

    @pytest.fixture
    def setup_data(self, app, db, session):
        """SalesOrder with one WorksOrder and one StockOrder, both Open."""
        TestSalesOrderClose._so_counter += 1
        c = TestSalesOrderClose._so_counter

        so = SalesOrder(
            so_number=f"SO-CLOSE-{c:03d}",
            customer_name="Test Customer",
            status="Open",
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.flush()

        item = Item(code=f"CLOSE-A{c}", description="Component A", category="Mechanical",
                    qty_on_hand=100.0, avg_cost=10.0, last_cost=10.0, active=True)
        session.add(item)
        session.flush()

        wo = WorksOrder(wo_number=f"WO-CLOSE-{c:03d}", so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        session.add(BOMLine(wo_id=wo.id, item_id=item.id, qty_required=1.0, unit_cost=10.0,
                            line_type="COMPONENT"))

        sto = StockOrder(stock_order_number=f"STO-CLOSE-{c:03d}", so_id=so.id, status="Open",
                         created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.flush()
        sto_line = StockOrderLine(stock_order_id=sto.id, item_code=item.code,
                                   description=item.description, qty=1.0)
        session.add(sto_line)
        session.commit()

        return {"so": so, "wo": wo, "sto": sto, "sto_line": sto_line}

    # ------------------------------------------------------------------
    # Manual close route
    # ------------------------------------------------------------------

    def test_close_blocked_while_wo_and_sto_open(self, client, app, setup_data):
        """POST /close is rejected while the WO and STO are still open."""
        so = setup_data["so"]
        resp = client.post(f"/sales-orders/{so.id}/close", follow_redirects=True)
        assert resp.status_code == 200
        assert b"still open" in resp.data

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Open"

    def test_close_succeeds_when_wo_and_sto_complete(self, client, app, db, session, setup_data):
        """POST /close succeeds once all WOs and STOs are Complete."""
        so, wo, sto = setup_data["so"], setup_data["wo"], setup_data["sto"]
        wo.status = "Complete"
        sto.status = "Complete"
        session.commit()

        resp = client.post(f"/sales-orders/{so.id}/close", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been closed" in resp.data

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Closed"

    def test_close_already_closed_is_idempotent(self, client, app, db, session, setup_data):
        """POST /close on an already-Closed order flashes a warning, no error."""
        so = setup_data["so"]
        so.status = "Closed"
        session.commit()

        resp = client.post(f"/sales-orders/{so.id}/close", follow_redirects=True)
        assert resp.status_code == 200
        assert b"already Closed" in resp.data

    # ------------------------------------------------------------------
    # Auto-close via WorksOrder.mark_complete
    # ------------------------------------------------------------------

    def test_mark_complete_autocloses_so_when_sto_already_complete(self, client, app, db, session, setup_data):
        """Completing the last open WO auto-closes the SO once the STO is also Complete."""
        so, wo, sto = setup_data["so"], setup_data["wo"], setup_data["sto"]
        sto.status = "Complete"
        session.commit()

        resp = client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Closed"

    def test_mark_complete_does_not_autoclose_while_sto_open(self, client, app, db, session, setup_data):
        """Completing the WO does not close the SO while the STO is still Open."""
        so, wo = setup_data["so"], setup_data["wo"]

        resp = client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Open"

    # ------------------------------------------------------------------
    # Auto-close via StockOrder.complete_order
    # ------------------------------------------------------------------

    def test_stock_order_complete_autocloses_so_when_wo_already_complete(self, client, app, db, session, setup_data):
        """Completing the last open STO auto-closes the SO once the WO is also Complete."""
        so, wo, sto, sto_line = setup_data["so"], setup_data["wo"], setup_data["sto"], setup_data["sto_line"]
        wo.status = "Complete"
        session.commit()

        client.post(
            f"/stock-orders/{sto.id}/pick",
            data={f"pick_qty_{sto_line.id}": "1.0", "picked_by": "Sam"},
            follow_redirects=True,
        )
        resp = client.post(f"/stock-orders/{sto.id}/complete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Closed"

    def test_stock_order_complete_does_not_autoclose_while_wo_open(self, client, app, db, session, setup_data):
        """Completing the STO does not close the SO while the WO is still Open."""
        so, sto, sto_line = setup_data["so"], setup_data["sto"], setup_data["sto_line"]

        client.post(
            f"/stock-orders/{sto.id}/pick",
            data={f"pick_qty_{sto_line.id}": "1.0", "picked_by": "Sam"},
            follow_redirects=True,
        )
        resp = client.post(f"/stock-orders/{sto.id}/complete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Open"
