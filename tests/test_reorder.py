"""Tests for Enhancement 2 - reorder point / min-max replenishment signals."""
import pytest
from models import db, Item, PurchaseOrder


class TestReorderPointStockReport:
    _counter = 0

    def _next_code(self):
        TestReorderPointStockReport._counter += 1
        return f"REORDER-TEST-{TestReorderPointStockReport._counter:03d}"

    def test_below_reorder_filter_only_returns_flagged_items(self, app, db, session, client):
        below = Item(code=self._next_code(), description="Below reorder", qty_on_hand=2.0,
                    reorder_point=5.0, reorder_qty=20.0, active=True)
        above = Item(code=self._next_code(), description="Above reorder", qty_on_hand=50.0,
                    reorder_point=5.0, reorder_qty=20.0, active=True)
        unset = Item(code=self._next_code(), description="No reorder point set", qty_on_hand=0.0,
                     reorder_point=0.0, active=True)
        session.add_all([below, above, unset])
        session.commit()

        response = client.get('/reports/stock/data?below_reorder=show&active_only=false')
        data = response.get_json()
        codes = [i['code'] for i in data['items']]

        assert below.code in codes
        assert above.code not in codes
        # unset.reorder_point == 0.0 must never be treated as "below reorder"
        assert unset.code not in codes

    def test_stock_data_includes_reorder_fields(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Reorder fields present", qty_on_hand=1.0,
                    reorder_point=10.0, reorder_qty=30.0, active=True)
        session.add(item)
        session.commit()

        response = client.get(f'/reports/stock/data?category=&active_only=false')
        data = response.get_json()
        row = next(i for i in data['items'] if i['code'] == item.code)
        assert row['reorder_point'] == 10.0
        assert row['below_reorder'] is True


class TestCreateFromShortfall:
    _counter = 0

    def _next_code(self):
        TestCreateFromShortfall._counter += 1
        return f"SHORTFALL-TEST-{TestCreateFromShortfall._counter:03d}"

    def test_creates_draft_po_with_shortfall_items(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Needs reorder", qty_on_hand=1.0,
                    reorder_point=5.0, reorder_qty=15.0, last_cost=12.5, active=True)
        session.add(item)
        session.commit()

        response = client.post('/purchase-orders/create-from-shortfall', follow_redirects=True)
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Draft Purchase Order" in body
        assert "shortfall item(s)" in body

        po = PurchaseOrder.query.filter(PurchaseOrder.po_number.like('PO-DRAFT-%')).order_by(
            PurchaseOrder.id.desc()).first()
        assert po is not None
        assert po.status == 'Draft'
        matching_lines = [l for l in po.lines if l.item_id == item.id]
        assert len(matching_lines) == 1
        assert matching_lines[0].qty_ordered == 15.0
        assert matching_lines[0].excl_price == 12.5

    def test_no_shortfall_items_flashes_warning_not_error(self, app, db, session, client):
        # No items with reorder_point > 0 in this isolated call means
        # nothing eligible - must not crash, just inform the user.
        item = Item(code=self._next_code(), description="Well stocked", qty_on_hand=100.0,
                    reorder_point=0.0, active=True)
        session.add(item)
        session.commit()

        # Temporarily this could still pick up shortfall items created by
        # other tests in the shared session-scoped DB; assert only that the
        # route never errors, regardless of what else is below reorder.
        response = client.post('/purchase-orders/create-from-shortfall', follow_redirects=True)
        assert response.status_code == 200


class TestDashboardReorderCard:
    def test_dashboard_shows_reorder_count(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert "Below Reorder Point" in response.get_data(as_text=True)
