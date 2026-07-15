"""Tests for production-receipt on Works Order Complete/Reopen.

Completing an ASSEMBLY WO whose assembly item is flagged
Item.is_stocked_finished_good=True credits that item's qty_on_hand with a
PRODUCTION movement; reopening reverses it via a REVERSAL movement.
Unflagged (default) assembly items must be left untouched — regression
guard for today's behavior.

See docs/specs/production-receipt-on-wo-complete.md.
"""
from datetime import datetime, timezone

from models import db, SalesOrder, WorksOrder, BOMLine, Item, StockMovement


class TestProductionReceipt:
    _c = 0

    def _next(self, prefix):
        TestProductionReceipt._c += 1
        return f"{prefix}-{TestProductionReceipt._c:03d}"

    def _setup(self, session, is_stocked_finished_good):
        so = SalesOrder(so_number=self._next("SO-PROD"), customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        assembly_item = Item(code=self._next("PROD-ASM"), description="Assembly Item",
                             qty_on_hand=10.0, active=True,
                             is_stocked_finished_good=is_stocked_finished_good)
        session.add(assembly_item)
        session.flush()

        wo = WorksOrder(wo_number=self._next("WO-PROD"), so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()

        assembly_line = BOMLine(wo_id=wo.id, item_id=assembly_item.id, qty_required=3.0,
                                unit_cost=0.0, line_type="ASSEMBLY_ITEM")
        session.add(assembly_line)
        session.commit()

        return {"so": so, "wo": wo, "assembly_item": assembly_item, "assembly_line": assembly_line}

    def test_complete_flagged_assembly_item_produces_stock(self, client, app, db, session):
        data = self._setup(session, is_stocked_finished_good=True)
        wo, assembly_item = data["wo"], data["assembly_item"]

        resp = client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            updated_item = db.session.get(Item, assembly_item.id)
            assert updated_item.qty_on_hand == 13.0  # 10 + qty_required (3)

            assembly_line = BOMLine.query.filter_by(wo_id=wo.id, line_type='ASSEMBLY_ITEM').first()
            assert assembly_line.qty_issued == 3.0

            movement = StockMovement.query.filter_by(item_id=assembly_item.id, movement_type='PRODUCTION').first()
            assert movement is not None
            assert movement.qty_change == 3.0
            assert movement.qty_after == 13.0
            assert movement.reference == wo.wo_number

    def test_complete_unflagged_assembly_item_leaves_qty_unchanged(self, client, app, db, session):
        data = self._setup(session, is_stocked_finished_good=False)
        wo, assembly_item = data["wo"], data["assembly_item"]

        resp = client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            updated_item = db.session.get(Item, assembly_item.id)
            assert updated_item.qty_on_hand == 10.0  # unchanged — default/current behavior

            assembly_line = BOMLine.query.filter_by(wo_id=wo.id, line_type='ASSEMBLY_ITEM').first()
            assert assembly_line.qty_issued == 0.0

            movement = StockMovement.query.filter_by(item_id=assembly_item.id, movement_type='PRODUCTION').first()
            assert movement is None

    def test_reopen_reverses_produced_stock(self, client, app, db, session):
        data = self._setup(session, is_stocked_finished_good=True)
        wo, assembly_item = data["wo"], data["assembly_item"]

        client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        with app.app_context():
            assert db.session.get(Item, assembly_item.id).qty_on_hand == 13.0

        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been reopened" in resp.data

        with app.app_context():
            updated_item = db.session.get(Item, assembly_item.id)
            assert updated_item.qty_on_hand == 10.0  # fully reversed

            assembly_line = BOMLine.query.filter_by(wo_id=wo.id, line_type='ASSEMBLY_ITEM').first()
            assert assembly_line.qty_issued == 0.0

            movement = StockMovement.query.filter_by(item_id=assembly_item.id, movement_type='REVERSAL').first()
            assert movement is not None
            assert movement.qty_change == -3.0
            assert movement.qty_after == 10.0

    def test_reopen_reverses_produced_stock_even_if_flag_later_cleared(self, client, app, db, session):
        """Reopen must key off qty_issued (what actually happened at Complete
        time), not the item's current is_stocked_finished_good value — the
        flag is mutable catalogue metadata and can change between Complete
        and Reopen. Otherwise a flag toggled off in between would leave the
        produced stock permanently un-reversed."""
        data = self._setup(session, is_stocked_finished_good=True)
        wo, assembly_item = data["wo"], data["assembly_item"]

        client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        with app.app_context():
            assert db.session.get(Item, assembly_item.id).qty_on_hand == 13.0

        # Toggle the flag off via the real Edit Item route (not a raw ORM
        # write), same code path an actual user would hit.
        edit_resp = client.post(f"/items/{assembly_item.id}/edit", data={
            'code': assembly_item.code,
            'description': assembly_item.description,
            'category': '',
            'active': 'on',
            'last_cost': '0',
            'avg_cost': '0',
            'excl_price': '0',
            'incl_price': '0',
        }, follow_redirects=True)
        assert edit_resp.status_code == 200
        with app.app_context():
            assert db.session.get(Item, assembly_item.id).is_stocked_finished_good is False

        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200

        with app.app_context():
            updated_item = db.session.get(Item, assembly_item.id)
            assert updated_item.qty_on_hand == 10.0  # still fully reversed

            assembly_line = BOMLine.query.filter_by(wo_id=wo.id, line_type='ASSEMBLY_ITEM').first()
            assert assembly_line.qty_issued == 0.0
