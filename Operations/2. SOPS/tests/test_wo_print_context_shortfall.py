"""Tests for services/doc_generator.get_works_order_print_context() —
demand-netted shortfall calc (Enhancement 3, task 4).

Covers the bug where the WO detail/print context computed shortfall from
raw Item.qty_on_hand only, ignoring qty_on_order (inbound POs) and
qty_committed (outstanding demand elsewhere). See
docs/specs/demand-netted-shortfall.md.
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
from services.doc_generator import get_works_order_print_context


class TestWOPrintContextShortfall:
    _c = 0

    def _make_item(self, session, qty_on_hand=0.0):
        TestWOPrintContextShortfall._c += 1
        item = Item(
            code=f"WOPC-{TestWOPrintContextShortfall._c:03d}",
            description="Test Item",
            qty_on_hand=qty_on_hand,
            active=True,
        )
        session.add(item)
        session.flush()
        return item

    def _make_so(self, session):
        TestWOPrintContextShortfall._c += 1
        so = SalesOrder(
            so_number=f"SO-WOPC-{TestWOPrintContextShortfall._c:03d}",
            customer_name="Test Customer",
            status="Open",
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.flush()
        return so

    def _make_wo(self, session, so, status='Open'):
        TestWOPrintContextShortfall._c += 1
        wo = WorksOrder(
            wo_number=f"WO-WOPC-{TestWOPrintContextShortfall._c:03d}",
            so_id=so.id,
            order_type="ASSEMBLY",
            status=status,
            issued_by="Tester",
            created_at=datetime.now(timezone.utc),
        )
        session.add(wo)
        session.flush()
        return wo

    def test_qty_on_order_covers_apparent_on_hand_shortfall(self, app, db, session):
        """Raw on-hand alone looks short, but an inbound PO covers it -> no shortfall.

        qty_issued == qty_required on this WO's own line so its remaining
        demand is 0 and it doesn't itself contribute to qty_committed
        (get_qty_committed_bulk sums outstanding demand from ALL open WOs
        system-wide, including this one) - isolates the on-order effect
        being tested from that self-referential contribution.
        """
        item = self._make_item(session, qty_on_hand=2.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)
        session.add(BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=10.0,
            line_type="COMPONENT",
        ))

        po = PurchaseOrder(
            po_number=f"PO-WOPC-{self._c}", supplier_name="Test Supplier",
            status="Open", created_at=datetime.now(timezone.utc),
        )
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=20.0, qty_received=0.0))
        session.commit()

        context = get_works_order_print_context(wo.id)
        line = context['flat_lines'][0]

        # 2 on hand + 20 on order - 0 committed = 22 available >= 10 required.
        assert line['qty_on_order'] == 20.0
        assert line['available_qty'] == 22.0
        assert line['shortfall'] == 0.0
        # qty_on_hand ground truth stays visible.
        assert line['qty_on_hand'] == 2.0

    def test_sufficient_on_hand_but_committed_elsewhere_flags_shortfall(self, app, db, session):
        """Raw on-hand alone looks sufficient, but it's fully committed to a
        different open Works Order -> shortfall > 0.

        qty_issued == qty_required on this WO's own line to isolate the
        "committed elsewhere" effect from this line's own contribution to
        qty_committed (see comment in the on-order test above).
        """
        item = self._make_item(session, qty_on_hand=10.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)
        session.add(BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=8.0, qty_issued=8.0,
            line_type="COMPONENT",
        ))

        # Different open WO also demanding this item.
        other_so = self._make_so(session)
        other_wo = self._make_wo(session, other_so)
        session.add(BOMLine(
            wo_id=other_wo.id, item_id=item.id, qty_required=9.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))
        session.commit()

        context = get_works_order_print_context(wo.id)
        line = context['flat_lines'][0]

        # 10 on hand + 0 on order - 9 committed elsewhere = 1 available < 8 required.
        assert line['qty_committed'] == 9.0
        assert line['available_qty'] == 1.0
        assert line['shortfall'] == 7.0
        assert line['qty_on_hand'] == 10.0

    def test_nested_component_qty_on_order_covers_shortfall(self, app, db, session):
        """Same as the on-order case above, but for a nested `components` line
        under an ASSEMBLY_ITEM parent — the bug existed in both loops."""
        parent_item = self._make_item(session, qty_on_hand=5.0)
        child_item = self._make_item(session, qty_on_hand=2.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)

        parent_line = BOMLine(
            wo_id=wo.id, item_id=parent_item.id, qty_required=1.0, qty_issued=0.0,
            line_type="ASSEMBLY_ITEM",
        )
        session.add(parent_line)
        session.flush()

        # qty_issued == qty_required so this line's own remaining demand is 0
        # and doesn't itself contribute to qty_committed (see comment on the
        # top-level on-order test above).
        child_line = BOMLine(
            wo_id=wo.id, item_id=child_item.id, qty_required=10.0, qty_issued=10.0,
            line_type="COMPONENT", parent_line_id=parent_line.id,
        )
        session.add(child_line)

        po = PurchaseOrder(
            po_number=f"PO-WOPC-{self._c}", supplier_name="Test Supplier",
            status="Open", created_at=datetime.now(timezone.utc),
        )
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=child_item.id, qty_ordered=15.0, qty_received=0.0))
        session.commit()

        context = get_works_order_print_context(wo.id)
        assert len(context['assembly_items']) == 1
        component = context['assembly_items'][0]['components'][0]

        # 2 on hand + 15 on order - 0 committed = 17 available >= 10 required.
        assert component['qty_on_order'] == 15.0
        assert component['available_qty'] == 17.0
        assert component['shortfall'] == 0.0

    def test_nested_component_committed_elsewhere_flags_shortfall(self, app, db, session):
        """Nested component line whose raw on-hand looks sufficient but is
        committed to another open Stock Order -> shortfall > 0."""
        parent_item = self._make_item(session, qty_on_hand=5.0)
        child_item = self._make_item(session, qty_on_hand=10.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)

        parent_line = BOMLine(
            wo_id=wo.id, item_id=parent_item.id, qty_required=1.0, qty_issued=0.0,
            line_type="ASSEMBLY_ITEM",
        )
        session.add(parent_line)
        session.flush()

        # qty_issued == qty_required so this line's own remaining demand is 0
        # and doesn't itself contribute to qty_committed (see comment on the
        # top-level on-order test above).
        child_line = BOMLine(
            wo_id=wo.id, item_id=child_item.id, qty_required=8.0, qty_issued=8.0,
            line_type="COMPONENT", parent_line_id=parent_line.id,
        )
        session.add(child_line)

        other_so = self._make_so(session)
        sto = StockOrder(
            stock_order_number=f"STO-WOPC-{self._c}", so_id=other_so.id,
            status="Open", created_at=datetime.now(timezone.utc),
        )
        session.add(sto)
        session.flush()
        session.add(StockOrderLine(
            stock_order_id=sto.id, item_code=child_item.code, description=child_item.description,
            qty=9.0, qty_issued=0.0,
        ))
        session.commit()

        context = get_works_order_print_context(wo.id)
        component = context['assembly_items'][0]['components'][0]

        # 10 on hand + 0 on order - 9 committed elsewhere = 1 available < 8 required.
        assert component['qty_committed'] == 9.0
        assert component['available_qty'] == 1.0
        assert component['shortfall'] == 7.0

    def test_own_line_outstanding_demand_not_self_counted(self, app, db, session):
        """Regression test for the self-counting bug: this WO's own line has
        OUTSTANDING demand (qty_issued < qty_required, unlike the other
        tests above which dodged the bug by fully issuing the own line).
        qty_on_hand exactly covers this WO's own requirement and nothing
        else in the system wants the item -> shortfall must be 0, not a
        false shortfall equal to the line's own remaining requirement.
        """
        item = self._make_item(session, qty_on_hand=10.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)
        session.add(BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=10.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))
        session.commit()

        context = get_works_order_print_context(wo.id)
        line = context['flat_lines'][0]

        # 10 on hand + 0 on order - 0 committed (own line excluded) = 10 available.
        assert line['qty_committed'] == 0.0
        assert line['available_qty'] == 10.0
        assert line['shortfall'] == 0.0

    def test_own_line_outstanding_demand_and_other_wo_both_reflected(self, app, db, session):
        """This WO's own outstanding demand is excluded from qty_committed,
        but a different open WO's demand for the same item still counts."""
        item = self._make_item(session, qty_on_hand=10.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)
        session.add(BOMLine(
            wo_id=wo.id, item_id=item.id, qty_required=8.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))

        other_so = self._make_so(session)
        other_wo = self._make_wo(session, other_so)
        session.add(BOMLine(
            wo_id=other_wo.id, item_id=item.id, qty_required=4.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))
        session.commit()

        context = get_works_order_print_context(wo.id)
        line = context['flat_lines'][0]

        # 10 on hand + 0 on order - 4 committed elsewhere (own line excluded) = 6 available.
        assert line['qty_committed'] == 4.0
        assert line['available_qty'] == 6.0
        assert line['shortfall'] == 2.0  # 8 required - 6 available

    def test_item_id_present_on_flat_and_nested_lines(self, app, db, session):
        """Regression test: item_id must be present on both a top-level
        flat_lines entry and a nested assembly_items[].components entry, so
        templates/works_orders/detail.html can link the item code to
        /items/<id> (see docs/specs/item-links-and-so-search-2026-07-15.md)."""
        flat_item = self._make_item(session, qty_on_hand=5.0)
        parent_item = self._make_item(session, qty_on_hand=1.0)
        child_item = self._make_item(session, qty_on_hand=3.0)
        so = self._make_so(session)
        wo = self._make_wo(session, so)

        session.add(BOMLine(
            wo_id=wo.id, item_id=flat_item.id, qty_required=1.0, qty_issued=0.0,
            line_type="COMPONENT",
        ))
        parent_line = BOMLine(
            wo_id=wo.id, item_id=parent_item.id, qty_required=1.0, qty_issued=0.0,
            line_type="ASSEMBLY_ITEM",
        )
        session.add(parent_line)
        session.flush()
        session.add(BOMLine(
            wo_id=wo.id, item_id=child_item.id, qty_required=1.0, qty_issued=0.0,
            line_type="COMPONENT", parent_line_id=parent_line.id,
        ))
        session.commit()

        context = get_works_order_print_context(wo.id)

        assert context['flat_lines'][0]['item_id'] == flat_item.id
        assert context['assembly_items'][0]['item_id'] == parent_item.id
        assert context['assembly_items'][0]['components'][0]['item_id'] == child_item.id
