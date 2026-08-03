"""Tests for the Stock Report route — demand-netted available_qty drives
the "Below Reorder Point" filter and general display (Enhancement 3).

See docs/specs/demand-netted-shortfall.md for the formula and rationale.
"""
from datetime import datetime, timezone

from models import (
    db,
    Item,
    SalesOrder,
    WorksOrder,
    BOMLine,
    PurchaseOrder,
    POLine,
)


class TestStockReportDemandNettedBelowReorder:
    _c = 0

    def _next_code(self, prefix):
        TestStockReportDemandNettedBelowReorder._c += 1
        return f"{prefix}-{TestStockReportDemandNettedBelowReorder._c:03d}"

    def test_fully_committed_item_flagged_below_reorder(self, app, db, session, client):
        # Raw qty_on_hand (20) sits comfortably above reorder_point (5), but
        # the item is fully committed to an open Works Order, so netted
        # available_qty (0) is at/below reorder_point. The old raw-qty
        # filter would have missed this; the netted filter must catch it.
        item = Item(code=self._next_code("STOCKRPT-COMMIT"), description="Fully committed item",
                    qty_on_hand=20.0, reorder_point=5.0, reorder_qty=30.0, active=True)
        session.add(item)
        session.flush()

        so = SalesOrder(so_number=self._next_code("SO-STOCKRPT"), customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        wo = WorksOrder(wo_number=self._next_code("WO-STOCKRPT"), so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        session.add(BOMLine(wo_id=wo.id, item_id=item.id, qty_required=20.0, qty_issued=0.0,
                            line_type="COMPONENT"))
        session.commit()

        response = client.get('/reports/stock/data?below_reorder=show&active_only=false')
        data = response.get_json()
        codes = [i['code'] for i in data['items']]

        assert item.code in codes

    def test_item_with_inbound_po_excluded_from_below_reorder(self, app, db, session, client):
        # Raw qty_on_hand (2) is at/below reorder_point (5), but a large
        # inbound Purchase Order pushes netted available_qty (32) back
        # above reorder_point. below_reorder=show must exclude it.
        item = Item(code=self._next_code("STOCKRPT-ONORDER"), description="Inbound stock item",
                    qty_on_hand=2.0, reorder_point=5.0, reorder_qty=30.0, active=True)
        session.add(item)
        session.flush()

        po = PurchaseOrder(po_number=self._next_code("PO-STOCKRPT"), supplier_name="Test Supplier",
                           status="Open", created_at=datetime.now(timezone.utc))
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=30.0, qty_received=0.0))
        session.commit()

        response = client.get('/reports/stock/data?below_reorder=show&active_only=false')
        data = response.get_json()
        codes = [i['code'] for i in data['items']]

        assert item.code not in codes

    def test_row_fields_present_and_numerically_consistent(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-FIELDS"), description="Field sanity item",
                    qty_on_hand=15.0, reorder_point=5.0, reorder_qty=30.0, active=True)
        session.add(item)
        session.flush()

        po = PurchaseOrder(po_number=self._next_code("PO-STOCKRPT-F"), supplier_name="Test Supplier",
                           status="Open", created_at=datetime.now(timezone.utc))
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=10.0, qty_received=0.0))

        so = SalesOrder(so_number=self._next_code("SO-STOCKRPT-F"), customer_name="Test Customer",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        wo = WorksOrder(wo_number=self._next_code("WO-STOCKRPT-F"), so_id=so.id, order_type="ASSEMBLY",
                        status="Open", issued_by="Tester", created_at=datetime.now(timezone.utc))
        session.add(wo)
        session.flush()
        session.add(BOMLine(wo_id=wo.id, item_id=item.id, qty_required=4.0, qty_issued=0.0,
                            line_type="COMPONENT"))
        session.commit()

        response = client.get(f'/reports/stock/data?active_only=false')
        data = response.get_json()
        row = next(i for i in data['items'] if i['code'] == item.code)

        assert row['qty_on_hand'] == 15.0
        assert row['qty_on_order'] == 10.0
        assert row['qty_committed'] == 4.0
        assert row['available_qty'] == 21.0
        assert row['available_qty'] == row['qty_on_hand'] + row['qty_on_order'] - row['qty_committed']

    def test_stock_export_csv_returns_valid_response(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-CSV"), description="CSV export item",
                    qty_on_hand=15.0, reorder_point=5.0, active=True)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/export-csv')
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert 'Available Qty' in body
        assert item.code in body

    def test_supplier_and_lead_time_weeks_present_in_stock_data(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-SUPPLIER"), description="Supplier field item",
                    qty_on_hand=10.0, active=True, supplier="Acme Supplies",
                    lead_time_weeks=2.5)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/data?active_only=false')
        data = response.get_json()
        row = next(i for i in data['items'] if i['code'] == item.code)

        assert row['supplier'] == 'Acme Supplies'
        assert row['lead_time_weeks'] == 2.5

    def test_supplier_and_lead_time_weeks_default_to_placeholder_when_unset(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-NOSUPPLIER"), description="No supplier item",
                    qty_on_hand=10.0, active=True)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/data?active_only=false')
        data = response.get_json()
        row = next(i for i in data['items'] if i['code'] == item.code)

        assert row['supplier'] == '-'
        assert row['lead_time_weeks'] == 0.0

    def test_supplier_and_lead_time_weeks_present_in_csv_export(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-SUPPLIER-CSV"), description="Supplier CSV item",
                    qty_on_hand=10.0, active=True, supplier="Acme Supplies",
                    lead_time_weeks=3.0)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/export-csv')
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert 'Supplier' in body
        assert 'Lead Time (weeks)' in body
        assert 'Acme Supplies' in body

    def test_amu_and_suggested_minmax_present_in_stock_data(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-AMU"), description="AMU field item",
                    qty_on_hand=10.0, active=True, amu=4.5,
                    suggested_min=2.0, suggested_max=10.0)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/data?active_only=false')
        data = response.get_json()
        row = next(i for i in data['items'] if i['code'] == item.code)

        assert row['amu'] == 4.5
        assert row['suggested_min'] == 2.0
        assert row['suggested_max'] == 10.0

    def test_amu_and_suggested_minmax_default_to_zero_when_unset(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-NOAMU"), description="No AMU item",
                    qty_on_hand=10.0, active=True)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/data?active_only=false')
        data = response.get_json()
        row = next(i for i in data['items'] if i['code'] == item.code)

        assert row['amu'] == 0.0
        assert row['suggested_min'] == 0
        assert row['suggested_max'] == 0

    def test_amu_and_suggested_minmax_present_in_csv_export(self, app, db, session, client):
        item = Item(code=self._next_code("STOCKRPT-AMU-CSV"), description="AMU CSV item",
                    qty_on_hand=10.0, active=True, amu=3.0,
                    suggested_min=1.0, suggested_max=6.0)
        session.add(item)
        session.commit()

        response = client.get('/reports/stock/export-csv')
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert 'AMU' in body
        assert 'Suggested Min' in body
        assert 'Suggested Max' in body
