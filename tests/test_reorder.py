"""Tests for Enhancement 2 - reorder point / min-max replenishment signals."""
import re
from datetime import datetime, timezone

import pytest
from models import db, Item, PurchaseOrder, POLine, SalesOrder, WorksOrder, BOMLine


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

    def test_item_covered_by_qty_on_order_excluded(self, app, db, session, client):
        # Raw qty_on_hand (2) is at/below reorder_point (5), but a large
        # inbound Purchase Order pushes netted available_qty back above
        # reorder_point - must not be added to the new draft PO (agreeing
        # with the Stock Report's below_reorder flag, which this button is
        # launched from).
        item = Item(code=self._next_code(), description="Covered by inbound PO", qty_on_hand=2.0,
                    reorder_point=5.0, reorder_qty=20.0, last_cost=10.0, active=True)
        session.add(item)
        session.flush()

        po = PurchaseOrder(po_number=f"PO-{item.code}", supplier_name="Test Supplier",
                           status="Open", created_at=datetime.now(timezone.utc))
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=10.0, qty_received=0.0))
        session.commit()

        response = client.post('/purchase-orders/create-from-shortfall', follow_redirects=True)
        assert response.status_code == 200

        draft_po = PurchaseOrder.query.filter(PurchaseOrder.po_number.like('PO-DRAFT-%')).order_by(
            PurchaseOrder.id.desc()).first()
        if draft_po is not None:
            matching_lines = [l for l in draft_po.lines if l.item_id == item.id]
            assert len(matching_lines) == 0

    def test_item_pushed_below_reorder_by_qty_committed_included(self, app, db, session, client):
        # Raw qty_on_hand (20) sits above reorder_point (5), but the item is
        # fully committed to an open Works Order, so netted available_qty
        # falls at/below reorder_point - must be added to the new draft PO.
        item = Item(code=self._next_code(), description="Pushed below reorder by demand",
                    qty_on_hand=20.0, reorder_point=5.0, reorder_qty=25.0, last_cost=8.0, active=True)
        session.add(item)
        session.flush()

        so = SalesOrder(so_number=f"SO-{item.code}", customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        wo = WorksOrder(wo_number=f"WO-{item.code}", so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        session.add(BOMLine(wo_id=wo.id, item_id=item.id, qty_required=20.0, qty_issued=0.0,
                            line_type="COMPONENT"))
        session.commit()

        response = client.post('/purchase-orders/create-from-shortfall', follow_redirects=True)
        assert response.status_code == 200

        draft_po = PurchaseOrder.query.filter(PurchaseOrder.po_number.like('PO-DRAFT-%')).order_by(
            PurchaseOrder.id.desc()).first()
        assert draft_po is not None
        matching_lines = [l for l in draft_po.lines if l.item_id == item.id]
        assert len(matching_lines) == 1
        assert matching_lines[0].qty_ordered == 25.0


class TestDashboardReorderCard:
    _counter = 0

    def _next_code(self):
        TestDashboardReorderCard._counter += 1
        return f"DASH-REORDER-{TestDashboardReorderCard._counter:03d}"

    def test_dashboard_shows_reorder_count(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert "Below Reorder Point" in response.get_data(as_text=True)

    def _reorder_stat_value(self, client):
        body = client.get('/').get_data(as_text=True)
        match = re.search(r'Below Reorder Point.*?stat-val">(\d+)<', body, re.DOTALL)
        assert match, "Could not find 'Below Reorder Point' stat on dashboard"
        return int(match.group(1))

    def test_reorder_count_nets_qty_on_order(self, app, db, session, client):
        """An item below raw qty_on_hand but covered by inbound qty_on_order
        (Enhancement 3 netting) must not inflate the dashboard's below-reorder
        stat - it should agree with the Stock Report's below_reorder calc."""
        before = self._reorder_stat_value(client)

        item = Item(code=self._next_code(), description="Below raw qty, covered by PO",
                    qty_on_hand=2.0, reorder_point=5.0, reorder_qty=20.0, active=True)
        session.add(item)
        session.flush()

        po = PurchaseOrder(po_number=f"PO-{item.code}", supplier_name="Test Supplier",
                           status="Open", created_at=datetime.now(timezone.utc))
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=10.0, qty_received=0.0))
        session.commit()

        # available_qty = 2 (on hand) + 10 (on order) - 0 (committed) = 12,
        # above the reorder_point of 5 - so despite raw qty_on_hand (2)
        # being below it, this item must not push the stat up.
        after = self._reorder_stat_value(client)
        assert after == before

        # Cross-check against the Stock Report, which shares the same
        # netting logic and is easier to assert against per-item.
        report = client.get('/reports/stock/data?active_only=false')
        row = next(i for i in report.get_json()['items'] if i['code'] == item.code)
        assert row['below_reorder'] is False


class TestItemReorderSettingsRoute:
    _counter = 0

    def _next_code(self):
        TestItemReorderSettingsRoute._counter += 1
        return f"REORDER-SETTINGS-TEST-{TestItemReorderSettingsRoute._counter:03d}"

    def test_update_reorder_settings(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Settings test", qty_on_hand=5.0, active=True)
        session.add(item)
        session.commit()

        response = client.post(f'/items/{item.id}/reorder-settings',
                               data={'reorder_point': '8', 'reorder_qty': '25'},
                               follow_redirects=True)
        assert response.status_code == 200
        assert "Reorder settings updated" in response.get_data(as_text=True)

        db.session.refresh(item)
        assert item.reorder_point == 8.0
        assert item.reorder_qty == 25.0

    def test_update_reorder_settings_rejects_non_numeric(self, app, db, session, client):
        item = Item(code=self._next_code(), description="Bad input test", qty_on_hand=5.0, active=True)
        session.add(item)
        session.commit()

        response = client.post(f'/items/{item.id}/reorder-settings',
                               data={'reorder_point': 'abc', 'reorder_qty': '25'},
                               follow_redirects=True)
        assert "must be numbers" in response.get_data(as_text=True)
