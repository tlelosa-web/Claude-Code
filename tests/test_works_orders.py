"""Tests for the Batch 34 'Released' status changes to routes/works_orders.py
(Sequencing item 13, docs/specs/sales-order-report-excel-export-2026-07-17.md
Decision 1 — Works Order subsection):

- print_order() flips Open -> Released exactly once, logging a single
  StatusChangeLog row; reprinting an already-Released (or later) WO does not
  re-flip or log a duplicate/no-op change.
- mark_complete() / cancel_order() / reopen_order() still work correctly
  starting from 'Released', not just 'Open', and each logs the real
  old/new status values.
- The 4 template-conditional sites in templates/works_orders/detail.html
  (Edit / Mark Complete / Confirm Pick / Delete) render their controls for a
  'Released' WO instead of hiding them.
"""
from datetime import datetime, timezone

from models import db, SalesOrder, WorksOrder, BOMLine, Item, StatusChangeLog


class TestWorksOrdersReleasedFlip:
    _c = 0

    def _next(self, prefix):
        TestWorksOrdersReleasedFlip._c += 1
        return f"{prefix}-{TestWorksOrdersReleasedFlip._c:03d}"

    def _setup_wo(self, session, order_type="ASSEMBLY", wo_status="Open"):
        so = SalesOrder(so_number=self._next("SO-WO34"), customer_name="Test Customer",
                         status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        item = Item(code=self._next("WO34-ITEM"), description="Component A",
                    qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()

        wo = WorksOrder(wo_number=self._next("WO34"), so_id=so.id, order_type=order_type,
                        status=wo_status, issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        bom_line = BOMLine(wo_id=wo.id, item_id=item.id, qty_required=10.0, unit_cost=5.0,
                           line_type="COMPONENT")
        session.add(bom_line)
        session.commit()

        return {"so": so, "wo": wo, "item": item, "bom_line": bom_line}

    def test_print_flips_open_to_released_once(self, client, app, db, session):
        data = self._setup_wo(session)
        wo = data["wo"]

        resp = client.get(f"/works-orders/{wo.id}/print")
        assert resp.status_code == 200

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Released"

            rows = StatusChangeLog.query.filter_by(
                order_id=wo.id, order_type="WO", field_name="status").all()
            assert len(rows) == 1
            assert rows[0].old_value == "Open"
            assert rows[0].new_value == "Released"

    def test_reprint_does_not_reflip_or_relog(self, client, app, db, session):
        data = self._setup_wo(session)
        wo = data["wo"]

        resp1 = client.get(f"/works-orders/{wo.id}/print")
        assert resp1.status_code == 200
        resp2 = client.get(f"/works-orders/{wo.id}/print")
        assert resp2.status_code == 200

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Released"

            rows = StatusChangeLog.query.filter_by(
                order_id=wo.id, order_type="WO", field_name="status").all()
            assert len(rows) == 1

    def test_print_does_not_downgrade_a_later_stage_wo(self, client, app, db, session):
        data = self._setup_wo(session, wo_status="Complete")
        wo = data["wo"]

        resp = client.get(f"/works-orders/{wo.id}/print")
        assert resp.status_code == 200

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Complete"

            rows = StatusChangeLog.query.filter_by(
                order_id=wo.id, order_type="WO", field_name="status").all()
            assert len(rows) == 0

    def test_mark_complete_from_released(self, client, app, db, session):
        data = self._setup_wo(session, wo_status="Released")
        wo, item = data["wo"], data["item"]

        resp = client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        assert resp.status_code == 200
        assert b"marked as Complete" in resp.data

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Complete"
            assert db.session.get(Item, item.id).qty_on_hand == 90.0

            rows = StatusChangeLog.query.filter_by(
                order_id=wo.id, order_type="WO", field_name="status").all()
            assert len(rows) == 1
            assert rows[0].old_value == "Released"
            assert rows[0].new_value == "Complete"

    def test_cancel_from_released(self, client, app, db, session):
        data = self._setup_wo(session, wo_status="Released")
        wo = data["wo"]

        resp = client.post(f"/works-orders/{wo.id}/cancel", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been cancelled" in resp.data

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Cancelled"

            rows = StatusChangeLog.query.filter_by(
                order_id=wo.id, order_type="WO", field_name="status").all()
            assert len(rows) == 1
            assert rows[0].old_value == "Released"
            assert rows[0].new_value == "Cancelled"

    def test_reopen_from_complete_logs_open_transition(self, client, app, db, session):
        data = self._setup_wo(session, wo_status="Released")
        wo = data["wo"]

        client.post(f"/works-orders/{wo.id}/complete", follow_redirects=True)
        resp = client.post(f"/works-orders/{wo.id}/reopen", follow_redirects=True)
        assert resp.status_code == 200
        assert b"has been reopened" in resp.data

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Open"

            rows = StatusChangeLog.query.filter_by(
                order_id=wo.id, order_type="WO", field_name="status").order_by(
                StatusChangeLog.id).all()
            # Open->Released (print not called here, so just Released->Complete->Open)
            assert rows[-1].old_value == "Complete"
            assert rows[-1].new_value == "Open"

    def test_confirm_pick_from_released_stock_order(self, client, app, db, session):
        data = self._setup_wo(session, order_type="STOCK", wo_status="Released")
        wo, item = data["wo"], data["item"]

        resp = client.post(f"/works-orders/{wo.id}/confirm-pick", follow_redirects=True)
        assert resp.status_code == 200
        assert b"confirmed" in resp.data

        with app.app_context():
            updated = db.session.get(WorksOrder, wo.id)
            assert updated.status == "Complete"
            assert db.session.get(Item, item.id).qty_on_hand == 90.0


class TestWorksOrdersReleasedTemplateGates:
    _c = 0

    def _next(self, prefix):
        TestWorksOrdersReleasedTemplateGates._c += 1
        return f"{prefix}-{TestWorksOrdersReleasedTemplateGates._c:03d}"

    def _setup_wo(self, session, order_type="ASSEMBLY"):
        so = SalesOrder(so_number=self._next("SO-WO34T"), customer_name="Test Customer",
                         status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        item = Item(code=self._next("WO34T-ITEM"), description="Component A",
                    qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()

        wo = WorksOrder(wo_number=self._next("WO34T"), so_id=so.id, order_type=order_type,
                        status="Released", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        bom_line = BOMLine(wo_id=wo.id, item_id=item.id, qty_required=10.0, unit_cost=5.0,
                           line_type="COMPONENT")
        session.add(bom_line)
        session.commit()
        return wo

    def test_detail_page_shows_edit_and_delete_for_released_assembly(self, client, session):
        wo = self._setup_wo(session, order_type="ASSEMBLY")

        resp = client.get(f"/works-orders/{wo.id}")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)

        assert f"/works-orders/{wo.id}/edit" in body
        assert f"/works-orders/{wo.id}/delete" in body
        assert f"/works-orders/{wo.id}/complete" in body
        assert "Cannot edit a completed or cancelled order" not in body
        assert "Cannot delete a completed or cancelled order" not in body

    def test_detail_page_shows_confirm_pick_for_released_stock_order(self, client, session):
        wo = self._setup_wo(session, order_type="STOCK")

        resp = client.get(f"/works-orders/{wo.id}")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)

        assert f"/works-orders/{wo.id}/confirm-pick" in body
        assert f"/works-orders/{wo.id}/edit" in body
        assert f"/works-orders/{wo.id}/delete" in body
