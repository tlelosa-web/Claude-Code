"""Regression test for bug sweep Fix 3 — confirm_pick() must guard against a
Cancelled STOCK-type Works Order the same way mark_complete() already does.

Not reachable via the current UI (the button only renders for Open/In
Progress on the detail page), but a direct POST to a cancelled STOCK-type WO
must not issue stock or silently un-cancel it.

See docs/specs/bug-sweep-2026-07-14.md (Fix 3).
"""
from datetime import datetime, timezone

from models import db, SalesOrder, WorksOrder, BOMLine, Item


class TestConfirmPickCancelledGuard:
    _c = 0

    def _next(self, prefix):
        TestConfirmPickCancelledGuard._c += 1
        return f"{prefix}-{TestConfirmPickCancelledGuard._c:03d}"

    def test_confirm_pick_on_cancelled_stock_order_is_blocked(self, app, db, session, client):
        so = SalesOrder(so_number=self._next("SO-CPICK"), customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        item = Item(code=self._next("CPICK-ITEM"), description="Picking guard item",
                    qty_on_hand=50.0, active=True)
        session.add(item)
        session.flush()

        wo = WorksOrder(wo_number=self._next("WO-CPICK"), so_id=so.id, order_type="STOCK",
                        status="Cancelled", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        bom_line = BOMLine(wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=0.0,
                           line_type="COMPONENT")
        session.add(bom_line)
        session.commit()

        response = client.post(f"/works-orders/{wo.id}/confirm-pick", follow_redirects=True)
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "cancelled and cannot be picked" in body

        db.session.refresh(wo)
        db.session.refresh(item)
        db.session.refresh(bom_line)

        assert wo.status == "Cancelled"
        assert item.qty_on_hand == 50.0
        assert bom_line.qty_issued == 0.0
