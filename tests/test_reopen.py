"""Tests for Reopen on Works Orders, Stock Orders, and Sales Orders — stock
reversal on Complete, no reversal needed on Cancelled, and the upward
SO cascade (child reopen -> parent SO reopen, but not the reverse).

See docs/specs/payment-status-delivery-date-reopen-columns.md (Part C).
"""
import pytest
from datetime import datetime, timezone
from models import db, SalesOrder, WorksOrder, StockOrder, StockOrderLine, BOMLine, Item, StockMovement


class TestReopenWorksOrder:
    _c = 0

    @pytest.fixture
    def setup_data(self, app, db, session):
        TestReopenWorksOrder._c += 1
        c = TestReopenWorksOrder._c

        so = SalesOrder(so_number=f"SO-REOPEN-WO-{c:03d}", customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        item = Item(code=f"REOPEN-WO-A{c}", description="Component A", qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()

        wo = WorksOrder(wo_number=f"WO-REOPEN-{c:03d}", so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        bom_line = BOMLine(wo_id=wo.id, item_id=item.id, qty_required=10.0, unit_cost=5.0,
                           line_type="COMPONENT")
        session.add(bom_line)
        session.commit()

        return {"so": so, "wo": wo, "item": item, "bom_line": bom_line}

    def test_reopen_complete_wo_reverses_stock(self, client, app, db, session, setup_data):
        so, wo, item = setup_data["so"], setup_data["wo"], setup_data["item"]

        # Complete the WO first — issues 10 units.
        resp = client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(Item, item.id).qty_on_hand == 90.0

        # Now reopen it.
        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been reopened" in resp.data

        with app.app_context():
            updated_item = db.session.get(Item, item.id)
            assert updated_item.qty_on_hand == 100.0  # fully reversed

            updated_wo = db.session.get(WorksOrder, wo.id)
            assert updated_wo.status == "Open"
            assert updated_wo.completed_at is None

            bom_line = BOMLine.query.filter_by(wo_id=wo.id).first()
            assert bom_line.qty_issued == 0.0

            movement = StockMovement.query.filter_by(item_id=item.id, movement_type='REVERSAL').first()
            assert movement is not None
            assert movement.qty_change == 10.0

    def test_reopen_cascades_parent_so_back_to_open(self, client, app, db, session, setup_data):
        so, wo = setup_data["so"], setup_data["wo"]

        client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Closed"

        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Open"

    def test_reopen_cancelled_wo_does_not_reverse_anything(self, client, app, db, session, setup_data):
        wo, item = setup_data["wo"], setup_data["item"]
        client.post(f"/works-orders/{wo.id}/cancel", follow_redirects=True)

        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(Item, item.id).qty_on_hand == 100.0  # unchanged
            assert db.session.get(WorksOrder, wo.id).status == "Open"

    def test_reopen_open_wo_is_rejected(self, client, app, setup_data):
        wo = setup_data["wo"]
        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"nothing to reopen" in resp.data

        with app.app_context():
            assert db.session.get(WorksOrder, wo.id).status == "Open"


class TestReopenStockOrder:
    _c = 0

    @pytest.fixture
    def setup_data(self, app, db, session):
        TestReopenStockOrder._c += 1
        c = TestReopenStockOrder._c

        so = SalesOrder(so_number=f"SO-REOPEN-STO-{c:03d}", customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        item = Item(code=f"REOPEN-STO-A{c}", description="Component A", qty_on_hand=50.0, active=True)
        session.add(item)
        session.flush()

        sto = StockOrder(stock_order_number=f"STO-REOPEN-{c:03d}", so_id=so.id, status="Open",
                         created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.flush()
        line = StockOrderLine(stock_order_id=sto.id, item_code=item.code,
                              description=item.description, qty=5.0)
        session.add(line)
        session.commit()

        return {"so": so, "sto": sto, "item": item, "line": line}

    def test_reopen_complete_sto_reverses_stock(self, client, app, db, session, setup_data):
        so, sto, item = setup_data["so"], setup_data["sto"], setup_data["item"]

        client.post(f"/stock-orders/{sto.id}/complete", follow_redirects=True)
        with app.app_context():
            assert db.session.get(Item, item.id).qty_on_hand == 45.0

        resp = client.post(f"/stock-orders/{sto.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been reopened" in resp.data

        with app.app_context():
            assert db.session.get(Item, item.id).qty_on_hand == 50.0
            assert db.session.get(StockOrder, sto.id).status == "Open"

            line = StockOrderLine.query.filter_by(stock_order_id=sto.id).first()
            assert line.qty_issued == 0.0

    def test_reopen_cascades_parent_so_back_to_open(self, client, app, db, session, setup_data):
        so, sto = setup_data["so"], setup_data["sto"]

        client.post(f"/stock-orders/{sto.id}/complete", follow_redirects=True)
        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Closed"

        resp = client.post(f"/stock-orders/{sto.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Open"

    def test_reopen_open_sto_is_rejected(self, client, app, setup_data):
        sto = setup_data["sto"]
        resp = client.post(f"/stock-orders/{sto.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"nothing to reopen" in resp.data


class TestReopenSalesOrder:
    _c = 0

    @pytest.fixture
    def setup_data(self, app, db, session):
        TestReopenSalesOrder._c += 1
        c = TestReopenSalesOrder._c
        so = SalesOrder(so_number=f"SO-REOPEN-SO-{c:03d}", customer_name="Test Customer",
                        status="Closed", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return {"so": so}

    def test_reopen_closed_so(self, client, app, db, session, setup_data):
        so = setup_data["so"]
        resp = client.post(f"/sales-orders/{so.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been reopened" in resp.data

        with app.app_context():
            assert db.session.get(SalesOrder, so.id).status == "Open"

    def test_reopen_non_closed_so_is_rejected(self, client, app, db, session, setup_data):
        so = setup_data["so"]
        so.status = "Open"
        session.commit()

        resp = client.post(f"/sales-orders/{so.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"nothing to reopen" in resp.data

    def test_reopen_so_does_not_cascade_to_children(self, client, app, db, session):
        """Reopening the SO itself must not force its WOs/STOs back open."""
        so = SalesOrder(so_number="SO-REOPEN-NOCASCADE-1", customer_name="Test Customer",
                        status="Closed", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        wo = WorksOrder(wo_number="WO-REOPEN-NOCASCADE-1", so_id=so.id, order_type="ASSEMBLY",
                        status="Complete", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.commit()

        resp = client.post(f"/sales-orders/{so.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            assert db.session.get(WorksOrder, wo.id).status == "Complete"  # unaffected
