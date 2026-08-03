"""Tests for services/demand.py — demand-netted qty_on_order, qty_committed,
and available_qty aggregate queries.

See docs/specs/demand-netted-shortfall.md for the formula and scope.
"""
from datetime import datetime, timezone

from models import (
    db,
    Item,
    SalesOrder,
    WorksOrder,
    BOMLine,
    StockOrder,
    StockOrderLine,
    PurchaseOrder,
    POLine,
)
from services.demand import (
    get_qty_on_order,
    get_qty_committed,
    get_qty_committed_bulk,
    get_available_qty,
)


class TestQtyOnOrder:
    _c = 0

    def _make_item(self, session, qty_on_hand=0.0):
        TestQtyOnOrder._c += 1
        item = Item(
            code=f"DEMAND-PO-{TestQtyOnOrder._c:03d}",
            description="Test Item",
            qty_on_hand=qty_on_hand,
            active=True,
        )
        session.add(item)
        session.flush()
        return item

    def _make_po(self, session, status='Open'):
        TestQtyOnOrder._c += 1
        po = PurchaseOrder(
            po_number=f"PO-DEMAND-{TestQtyOnOrder._c:03d}",
            supplier_name="Test Supplier",
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        session.add(po)
        session.flush()
        return po

    def test_no_open_orders_returns_zero(self, app, db, session):
        item = self._make_item(session)
        session.commit()

        assert get_qty_on_order(item.id) == 0.0

    def test_open_po_not_received_full_qty(self, app, db, session):
        item = self._make_item(session)
        po = self._make_po(session, status='Open')
        line = POLine(po_id=po.id, item_id=item.id, qty_ordered=50.0, qty_received=0.0)
        session.add(line)
        session.commit()

        assert get_qty_on_order(item.id) == 50.0

    def test_partially_received_po_remainder_only(self, app, db, session):
        item = self._make_item(session)
        po = self._make_po(session, status='Partially Received')
        line = POLine(po_id=po.id, item_id=item.id, qty_ordered=50.0, qty_received=20.0)
        session.add(line)
        session.commit()

        assert get_qty_on_order(item.id) == 30.0

    def test_received_po_excluded(self, app, db, session):
        item = self._make_item(session)
        po = self._make_po(session, status='Received')
        line = POLine(po_id=po.id, item_id=item.id, qty_ordered=50.0, qty_received=50.0)
        session.add(line)
        session.commit()

        assert get_qty_on_order(item.id) == 0.0

    def test_cancelled_po_excluded(self, app, db, session):
        item = self._make_item(session)
        po = self._make_po(session, status='Cancelled')
        line = POLine(po_id=po.id, item_id=item.id, qty_ordered=50.0, qty_received=0.0)
        session.add(line)
        session.commit()

        assert get_qty_on_order(item.id) == 0.0

    def test_multiple_open_po_lines_summed(self, app, db, session):
        item = self._make_item(session)
        po1 = self._make_po(session, status='Open')
        po2 = self._make_po(session, status='Partially Received')
        session.add(POLine(po_id=po1.id, item_id=item.id, qty_ordered=10.0, qty_received=0.0))
        session.add(POLine(po_id=po2.id, item_id=item.id, qty_ordered=20.0, qty_received=5.0))
        session.commit()

        assert get_qty_on_order(item.id) == 25.0  # 10 + 15


class TestQtyCommitted:
    _c = 0

    def _make_item(self, session, qty_on_hand=0.0):
        TestQtyCommitted._c += 1
        item = Item(
            code=f"DEMAND-CM-{TestQtyCommitted._c:03d}",
            description="Test Item",
            qty_on_hand=qty_on_hand,
            active=True,
        )
        session.add(item)
        session.flush()
        return item

    def _make_so(self, session):
        TestQtyCommitted._c += 1
        so = SalesOrder(
            so_number=f"SO-DEMAND-{TestQtyCommitted._c:03d}",
            customer_name="Test Customer",
            status="Open",
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.flush()
        return so

    def _make_wo(self, session, so, status='Open'):
        TestQtyCommitted._c += 1
        wo = WorksOrder(
            wo_number=f"WO-DEMAND-{TestQtyCommitted._c:03d}",
            so_id=so.id,
            order_type="ASSEMBLY",
            status=status,
            issued_by="Tester",
            created_at=datetime.now(timezone.utc),
        )
        session.add(wo)
        session.flush()
        return wo

    def _make_sto(self, session, so, status='Open'):
        TestQtyCommitted._c += 1
        sto = StockOrder(
            stock_order_number=f"STO-DEMAND-{TestQtyCommitted._c:03d}",
            so_id=so.id,
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        session.add(sto)
        session.flush()
        return sto

    def test_no_open_demand_returns_zero(self, app, db, session):
        item = self._make_item(session)
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_open_wo_line_partially_issued_remainder_only(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='Open')
        bom_line = BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=4.0,
            line_type="COMPONENT",
        )
        session.add(bom_line)
        session.commit()

        assert get_qty_committed(item.id) == 6.0

    def test_in_progress_wo_counted(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='In Progress')
        bom_line = BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=8.0, qty_issued=0.0,
            line_type="COMPONENT",
        )
        session.add(bom_line)
        session.commit()

        assert get_qty_committed(item.id) == 8.0

    def test_complete_wo_excluded(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='Complete')
        bom_line = BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=10.0,
            line_type="COMPONENT",
        )
        session.add(bom_line)
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_cancelled_wo_excluded(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='Cancelled')
        bom_line = BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=0.0,
            line_type="COMPONENT",
        )
        session.add(bom_line)
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_assembly_item_line_excluded(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='Open')
        bom_line = BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=1.0, qty_issued=0.0,
            line_type="ASSEMBLY_ITEM",
        )
        session.add(bom_line)
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_open_sto_line_partially_issued_remainder_only(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        sto = self._make_sto(session, so, status='Open')
        line = StockOrderLine(
            stock_order_id=sto.id, item_code=item.code, description=item.description,
            qty=20.0, qty_issued=5.0,
        )
        session.add(line)
        session.commit()

        assert get_qty_committed(item.id) == 15.0

    def test_complete_sto_excluded(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        sto = self._make_sto(session, so, status='Complete')
        line = StockOrderLine(
            stock_order_id=sto.id, item_code=item.code, description=item.description,
            qty=20.0, qty_issued=20.0,
        )
        session.add(line)
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_cancelled_sto_excluded(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        sto = self._make_sto(session, so, status='Cancelled')
        line = StockOrderLine(
            stock_order_id=sto.id, item_code=item.code, description=item.description,
            qty=20.0, qty_issued=0.0,
        )
        session.add(line)
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_wo_and_sto_demand_summed(self, app, db, session):
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='Open')
        session.add(BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))
        sto = self._make_sto(session, so, status='Open')
        session.add(StockOrderLine(
            stock_order_id=sto.id, item_code=item.code, description=item.description,
            qty=5.0, qty_issued=0.0,
        ))
        session.commit()

        assert get_qty_committed(item.id) == 15.0

    def test_exclude_wo_id_omits_that_wos_own_demand(self, app, db, session):
        """exclude_wo_id excludes only that WO's own BOMLine demand — a
        different open WO's demand for the same item still counts."""
        item = self._make_item(session)
        so = self._make_so(session)

        own_wo = self._make_wo(session, so, status='Open')
        session.add(BOMLine(
            wo_id=own_wo.id, item_id=item.id, qty_required=10.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))

        other_wo = self._make_wo(session, so, status='Open')
        session.add(BOMLine(
            wo_id=other_wo.id, item_id=item.id, qty_required=6.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))
        session.commit()

        # Without exclusion, both lines count.
        assert get_qty_committed_bulk(item_ids=[item.id]).get(item.id, 0.0) == 16.0

        # With exclusion, only the other WO's demand counts.
        result = get_qty_committed_bulk(item_ids=[item.id], exclude_wo_id=own_wo.id)
        assert result.get(item.id, 0.0) == 6.0

    def test_wo_line_over_issued_floors_at_zero_not_negative(self, app, db, session):
        """An Open WO line where qty_issued > qty_required (hand-edited row
        or partial-reversal edge case) must contribute 0, not negative,
        outstanding demand - a negative contribution would reduce total
        committed and inflate available_qty in the wrong direction."""
        item = self._make_item(session)
        so = self._make_so(session)
        wo = self._make_wo(session, so, status='Open')
        session.add(BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=5.0, qty_issued=8.0,
            line_type="COMPONENT",
        ))
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_sto_line_over_issued_floors_at_zero_not_negative(self, app, db, session):
        """Same over-issued edge case on the Stock Order side."""
        item = self._make_item(session)
        so = self._make_so(session)
        sto = self._make_sto(session, so, status='Open')
        session.add(StockOrderLine(
            stock_order_id=sto.id, item_code=item.code, description=item.description,
            qty=5.0, qty_issued=9.0,
        ))
        session.commit()

        assert get_qty_committed(item.id) == 0.0

    def test_exclude_sto_id_omits_that_stos_own_demand(self, app, db, session):
        """exclude_sto_id excludes only that STO's own line demand — a
        different open STO's demand for the same item still counts."""
        item = self._make_item(session)
        so = self._make_so(session)

        own_sto = self._make_sto(session, so, status='Open')
        session.add(StockOrderLine(
            stock_order_id=own_sto.id, item_code=item.code, description=item.description,
            qty=20.0, qty_issued=0.0,
        ))

        other_sto = self._make_sto(session, so, status='Open')
        session.add(StockOrderLine(
            stock_order_id=other_sto.id, item_code=item.code, description=item.description,
            qty=5.0, qty_issued=0.0,
        ))
        session.commit()

        # Without exclusion, both lines count.
        assert get_qty_committed_bulk(item_ids=[item.id]).get(item.id, 0.0) == 25.0

        # With exclusion, only the other STO's demand counts.
        result = get_qty_committed_bulk(item_ids=[item.id], exclude_sto_id=own_sto.id)
        assert result.get(item.id, 0.0) == 5.0


class TestAvailableQty:
    _c = 0

    def test_combines_on_hand_on_order_and_committed(self, app, db, session):
        TestAvailableQty._c += 1
        c = TestAvailableQty._c

        item = Item(code=f"DEMAND-AV-{c:03d}", description="Test Item",
                   qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()

        # 30 units inbound on an open PO.
        po = PurchaseOrder(po_number=f"PO-DEMAND-AV-{c:03d}", supplier_name="Test Supplier",
                           status="Open", created_at=datetime.now(timezone.utc))
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=30.0, qty_received=0.0))

        # 40 units committed to an open Works Order.
        so = SalesOrder(so_number=f"SO-DEMAND-AV-{c:03d}", customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        wo = WorksOrder(wo_number=f"WO-DEMAND-AV-{c:03d}", so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        session.add(BOMLine(wo_id=wo.id, item_id=item.id, qty_required=40.0, qty_issued=0.0,
                            line_type="COMPONENT"))
        session.commit()

        # 100 on hand + 30 on order - 40 committed = 90 available.
        assert get_available_qty(item.id) == 90.0
