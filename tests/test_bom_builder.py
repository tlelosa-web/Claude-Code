"""Tests for bom_builder module."""
import json
import re
import pytest
from datetime import datetime, timezone, date
from models import (
    db, Item, SalesOrder, WorksOrder, BOMLine, SOLineItem,
    PurchaseOrder, POLine,
)

class TestBOMBuilder:
    _so_counter = 0
    
    @pytest.fixture
    def setup_data(self, app, db, session):
        """Set up test data with unique SO number and item codes."""
        TestBOMBuilder._so_counter += 1
        c = TestBOMBuilder._so_counter
        
        # Create sales order
        so = SalesOrder(so_number=f"SO-TEST-{c:03d}", reference="REF001", customer_name="Test Customer",
                        status='Draft', created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        
        # Create test items with unique codes per test run
        items_data = {
            'comp_a': Item(code=f"BOM-A{c}", description="Component A", category="Electronics", 
                 qty_on_hand=100.0, avg_cost=50.0, last_cost=45.0, active=True),
            'comp_b': Item(code=f"BOM-B{c}", description="Component B", category="Mechanical",
                 qty_on_hand=5.0, avg_cost=30.0, last_cost=28.0, active=True),
            'comp_c': Item(code=f"BOM-C{c}", description="Component C (Low Stock)", category="Hardware",
                 qty_on_hand=2.0, avg_cost=15.0, last_cost=12.0, active=True),
        }
        for item in items_data.values():
            session.add(item)
        session.flush()
        
        return {
            'so': so,
            'items': items_data,
            'so_id': so.id,
        }
    
    def test_create_works_order(self, app, db, session, setup_data):
        """Test that a WorksOrder record is created with correct fields."""
        from services.bom_builder import create_works_order_or_picking_list
        
        data = setup_data
        items_list = [
            {'item_id': data['items']['comp_a'].id, 'qty_required': 2.0, 'notes': 'Main board'},
            {'item_id': data['items']['comp_b'].id, 'qty_required': 4.0, 'notes': 'Mounting brackets'},
        ]
        
        wo = create_works_order_or_picking_list(data['so_id'], 'ASSEMBLY', items_list, 'Test User')
        
        assert wo is not None
        assert wo.order_type == 'ASSEMBLY'
        assert wo.status == 'Open'
        assert wo.issued_by == 'Test User'
        assert wo.so_id == data['so_id']
        assert wo.wo_number.startswith('WO-')
        
        # Check BOM lines were created
        bom_lines = BOMLine.query.filter_by(wo_id=wo.id).all()
        assert len(bom_lines) == 2
        
        # Check unit costs were set from avg_cost
        for line in bom_lines:
            item = db.session.get(Item, line.item_id)
            assert line.unit_cost == item.avg_cost
    
    def test_create_picking_list(self, app, db, session, setup_data):
        """Test that a STOCK order creates a Picking List."""
        from services.bom_builder import create_works_order_or_picking_list
        
        data = setup_data
        items_list = [
            {'item_id': data['items']['comp_a'].id, 'qty_required': 1.0, 'notes': ''},
        ]
        
        wo = create_works_order_or_picking_list(data['so_id'], 'STOCK', items_list, 'Store Clerk')
        
        assert wo.order_type == 'STOCK'
        assert wo.wo_number.startswith('WO-')
        assert wo.issued_by == 'Store Clerk'
    
    def test_shortfall_detected(self, app, db, session, setup_data):
        """Test that shortfall is detected when qty_required > qty_on_hand."""
        from services.bom_builder import create_works_order_or_picking_list
        
        data = setup_data
        # Component C has only 2 on hand, require 10
        items_list = [
            {'item_id': data['items']['comp_c'].id, 'qty_required': 10.0, 'notes': 'Needs more than available'},
        ]
        
        wo = create_works_order_or_picking_list(data['so_id'], 'ASSEMBLY', items_list, 'Test User')
        
        # Check BOM line
        bom_line = BOMLine.query.filter_by(wo_id=wo.id).first()
        assert bom_line is not None
        assert bom_line.qty_required == 10.0
        
        # Shortfall = qty_required - qty_on_hand = 10 - 2 = 8
        item = db.session.get(Item, bom_line.item_id)
        shortfall = max(0.0, bom_line.qty_required - item.qty_on_hand)
        assert shortfall == 8.0
    
    def test_total_cost_calculation(self, app, db, session, setup_data):
        """Test that cost fields are removed from print context."""
        from services.bom_builder import create_works_order_or_picking_list
        from services.doc_generator import get_works_order_print_context
        
        data = setup_data
        items_list = [
            {'item_id': data['items']['comp_a'].id, 'qty_required': 3.0, 'notes': ''},
            {'item_id': data['items']['comp_b'].id, 'qty_required': 2.0, 'notes': ''},
        ]
        
        wo = create_works_order_or_picking_list(data['so_id'], 'ASSEMBLY', items_list, 'Test User')
        
        # Get print context
        context = get_works_order_print_context(wo.id)
        
        # Verify cost fields are NOT present
        assert 'total_excl_cost' not in context
        
        # Verify new structure: assembly_items and flat_lines
        assert 'assembly_items' in context
        assert 'flat_lines' in context
        
        # All items should be in flat_lines (no nested structure in this test)
        assert len(context['flat_lines']) == 2
        assert len(context['assembly_items']) == 0
        
        # Verify individual lines don't have cost fields
        for line in context['flat_lines']:
            assert 'unit_cost' not in line
            assert 'total_cost' not in line

    def test_build_bom_page_renders_item_catalogue(self, client, session, setup_data):
        """BOM builder page should JSON-render item catalogue data for the UI."""
        so = setup_data['so']

        response = client.get(f"/sales-orders/{so.id}/build-bom")
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "Build Works Pack" in body
        assert "catalogueItems" in body
        assert "Object of type Item is not JSON serializable" not in body
        assert setup_data['items']['comp_a'].code in body
        assert "Save Works Pack" in body

    def test_build_bom_persists_fan_as_assembly_parent(self, client, db, session, setup_data):
        """Fan line selected in build-bom is saved as an ASSEMBLY_ITEM parent with
        its components nested beneath, so the print context renders a header row."""
        from services.doc_generator import get_works_order_print_context
        from models import SOLineItem

        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']  # resolves to the fan/assembly item
        comp_b = data['items']['comp_b']
        comp_c = data['items']['comp_c']

        # SO line whose parsed code ("BOM-A..") resolves to comp_a, marked as fan
        fan_line = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Fan Assembly", qty=1.0)
        session.add(fan_line)
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{fan_line.id}": "fan",
            f"line_job_number_{fan_line.id}": "FM0001",
            "issued_by": "Tester",
            "component_item_id[]": [str(comp_b.id), str(comp_c.id)],
            "component_qty[]": ["4", "6"],
        })
        assert resp.status_code in (200, 302)

        wo = WorksOrder.query.filter_by(so_id=so.id).first()
        assert wo is not None

        # Assembly parent persisted; components re-parented under it
        assemblies = BOMLine.query.filter_by(wo_id=wo.id, line_type='ASSEMBLY_ITEM').all()
        assert len(assemblies) == 1
        assert assemblies[0].item_id == comp_a.id
        children = BOMLine.query.filter_by(parent_line_id=assemblies[0].id).all()
        assert len(children) == 2
        assert all(ch.line_type == 'COMPONENT' for ch in children)

        # Print context surfaces a single assembly header with nested components
        ctx = get_works_order_print_context(wo.id)
        assert len(ctx['assembly_items']) == 1
        assert len(ctx['assembly_items'][0]['components']) == 2
        assert ctx['flat_lines'] == []

    def test_build_bom_creates_separate_wo_per_fan_line(self, client, db, session, setup_data):
        """Multiple Fan lines on one SO (e.g. several fan models on one order)
        each become their own Works Order, with components scoped to whichever
        Fan line they were assigned to via the per-row dropdown."""
        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']  # fan #1 assembly item
        comp_b = data['items']['comp_b']  # component for fan #1 only
        comp_c = data['items']['comp_c']  # component for fan #2 only

        fan_2_item = Item(code=f"BOM-FAN2-{so.id}", description="Second Fan Model",
                           category="Fans", qty_on_hand=10.0, avg_cost=200.0, last_cost=180.0, active=True)
        session.add(fan_2_item)
        session.flush()

        fan_line_1 = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Fan Assembly 1", qty=2.0)
        fan_line_2 = SOLineItem(so_id=so.id, description=f"{fan_2_item.code} - Fan Assembly 2", qty=3.0)
        session.add_all([fan_line_1, fan_line_2])
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{fan_line_1.id}": "fan",
            f"line_role_{fan_line_2.id}": "fan",
            f"line_job_number_{fan_line_1.id}": "FM0002",
            f"line_job_number_{fan_line_2.id}": "FM0003",
            "issued_by": "Tester",
            "component_item_id[]": [str(comp_b.id), str(comp_c.id)],
            "component_qty[]": ["4", "6"],
            "component_fan_line_id[]": [str(fan_line_1.id), str(fan_line_2.id)],
        })
        assert resp.status_code in (200, 302)
        body = resp.get_data(as_text=True)
        assert "Only one line can be marked as Fan" not in body

        wos = WorksOrder.query.filter_by(so_id=so.id).order_by(WorksOrder.id).all()
        assert len(wos) == 2
        assert wos[0].wo_number != wos[1].wo_number

        assembly_1 = BOMLine.query.filter_by(wo_id=wos[0].id, line_type='ASSEMBLY_ITEM').first()
        assert assembly_1.item_id == comp_a.id
        children_1 = BOMLine.query.filter_by(parent_line_id=assembly_1.id).all()
        assert len(children_1) == 1
        assert children_1[0].item_id == comp_b.id

        assembly_2 = BOMLine.query.filter_by(wo_id=wos[1].id, line_type='ASSEMBLY_ITEM').first()
        assert assembly_2.item_id == fan_2_item.id
        children_2 = BOMLine.query.filter_by(parent_line_id=assembly_2.id).all()
        assert len(children_2) == 1
        assert children_2[0].item_id == comp_c.id

    def test_build_bom_requires_job_number_for_assembly(self, client, db, session, setup_data):
        """A Fan line with no FM/job number is rejected — no WorksOrder is created."""
        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']

        fan_line = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Fan Assembly", qty=1.0)
        session.add(fan_line)
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{fan_line.id}": "fan",
            "issued_by": "Tester",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"FM / Job number is required" in resp.data

        assert WorksOrder.query.filter_by(so_id=so.id).first() is None

    def test_build_bom_saves_job_number_on_assembly(self, client, db, session, setup_data):
        """A supplied FM/job number is persisted onto the Sales Order once the WO is created."""
        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']

        fan_line = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Fan Assembly", qty=1.0)
        session.add(fan_line)
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{fan_line.id}": "fan",
            f"line_job_number_{fan_line.id}": "FM9999",
            "issued_by": "Tester",
        })
        assert resp.status_code in (200, 302)

        assert WorksOrder.query.filter_by(so_id=so.id).first() is not None
        updated_so = db.session.get(SalesOrder, so.id)
        assert updated_so.job_numbers == "FM9999"

    def test_build_bom_sets_works_order_job_number_per_fan_line(self, client, db, session, setup_data):
        """Each WorksOrder created from a multi-fan build carries the FM number
        of the specific Fan line it originated from, not the other fan's."""
        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']

        fan_2_item = Item(code=f"BOM-FAN2-JN-{so.id}", description="Second Fan Model",
                           category="Fans", qty_on_hand=10.0, avg_cost=200.0, last_cost=180.0, active=True)
        session.add(fan_2_item)
        session.flush()

        fan_line_1 = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Fan Assembly 1", qty=2.0)
        fan_line_2 = SOLineItem(so_id=so.id, description=f"{fan_2_item.code} - Fan Assembly 2", qty=3.0)
        session.add_all([fan_line_1, fan_line_2])
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{fan_line_1.id}": "fan",
            f"line_role_{fan_line_2.id}": "fan",
            f"line_job_number_{fan_line_1.id}": "FM1001",
            f"line_job_number_{fan_line_2.id}": "FM1002",
            "issued_by": "Tester",
        })
        assert resp.status_code in (200, 302)

        wos = WorksOrder.query.filter_by(so_id=so.id).order_by(WorksOrder.id).all()
        assert len(wos) == 2
        assert wos[0].job_number == "FM1001"
        assert wos[1].job_number == "FM1002"

    def test_build_bom_saves_optional_job_number_on_stock_lines(self, client, db, session, setup_data):
        """Stock lines can optionally carry an FM number, persisted onto the
        StockOrderLine (not required, unlike Fan lines)."""
        from models import StockOrder, StockOrderLine

        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']

        stock_line = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Spare Part", qty=1.0)
        session.add(stock_line)
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{stock_line.id}": "stock",
            f"line_job_number_{stock_line.id}": "FM2002",
        })
        assert resp.status_code == 302

        sto = StockOrder.query.filter_by(so_id=so.id).first()
        assert sto is not None
        line = StockOrderLine.query.filter_by(stock_order_id=sto.id).first()
        assert line.job_number == "FM2002"
        assert sto.job_numbers == "FM2002"

    def test_build_bom_stock_only_does_not_require_job_number(self, client, db, session, setup_data):
        """Stock-only builds (no Fan lines) must not be blocked by a missing FM number."""
        from models import StockOrder

        data = setup_data
        so = data['so']
        comp_a = data['items']['comp_a']

        stock_line = SOLineItem(so_id=so.id, description=f"{comp_a.code} - Spare Part", qty=1.0)
        session.add(stock_line)
        session.flush()

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{stock_line.id}": "stock",
        })
        # Redirects to the SO detail page on success, not back to build-bom
        # with a validation error.
        assert resp.status_code == 302
        assert "/build-bom" not in resp.headers.get("Location", "")

        assert StockOrder.query.filter_by(so_id=so.id).first() is not None


class TestBOMBuilderDemandNettedAvailability:
    """Enhancement 3 (demand-netted shortfall) — BOM Builder catalogue JSON.

    item_to_bom_json() is served to the browser via the Works Order "edit"
    page (routes/works_orders.py edit_order), which bulk-fetches
    qty_on_order / qty_committed / next_po_due once for the whole catalogue
    and passes them through. These tests hit that route and inspect the
    served `items` JSON payload for the demand-netting fields.
    """
    _c = 0

    def _next_code(self, prefix):
        TestBOMBuilderDemandNettedAvailability._c += 1
        return f"{prefix}-{TestBOMBuilderDemandNettedAvailability._c:04d}"

    def _make_so(self, session):
        so = SalesOrder(
            so_number=self._next_code("SO-NET"),
            customer_name="Test Customer",
            status="Open",
            created_at=datetime.now(timezone.utc),
        )
        session.add(so)
        session.flush()
        return so

    def _make_open_wo(self, session, so):
        wo = WorksOrder(
            wo_number=self._next_code("WO-NET"),
            so_id=so.id,
            order_type="ASSEMBLY",
            status="Open",
            issued_by="Tester",
            created_at=datetime.now(timezone.utc),
        )
        session.add(wo)
        session.flush()
        return wo

    def _get_catalogue_items(self, client, wo_id):
        """GET the Works Order edit page and pull the `items` JSON payload
        out of the embedded window.SOPS_EDIT config."""
        resp = client.get(f"/works-orders/{wo_id}/edit")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)

        match = re.search(r"items:\s*(\[.*?\]),\s*\n\s*woId", body, re.DOTALL)
        assert match is not None, "Could not find items JSON in edit page"
        return json.loads(match.group(1))

    def _find_item(self, catalogue_items, code):
        for entry in catalogue_items:
            if entry['code'] == code:
                return entry
        raise AssertionError(f"Item {code} not found in served catalogue JSON")

    def test_shortfall_on_hand_covered_by_open_po(self, app, db, session, client):
        """Item is short on qty_on_hand alone, but an open PO covers it —
        available_qty in the served JSON reflects the inbound stock."""
        item = Item(code=self._next_code("NET-PO"), description="PO Covered Item",
                    category="Hardware", qty_on_hand=2.0, active=True)
        session.add(item)
        session.flush()

        po = PurchaseOrder(po_number=self._next_code("PO-NET"), supplier_name="Test Supplier",
                           status="Open", due_date=date(2026, 8, 1),
                           created_at=datetime.now(timezone.utc))
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, qty_ordered=20.0, qty_received=0.0))

        so = self._make_so(session)
        wo = self._make_open_wo(session, so)
        session.commit()

        catalogue = self._get_catalogue_items(client, wo.id)
        served = self._find_item(catalogue, item.code)

        assert served['qty_on_hand'] == 2.0
        assert served['qty_on_order'] == 20.0
        assert served['qty_committed'] == 0.0
        assert served['available_qty'] == 22.0  # 2 + 20 - 0, covers a 10-unit requirement
        assert served['next_po_due'] == '2026-08-01'

    def test_available_qty_reduced_by_other_open_order_commitment(self, app, db, session, client):
        """Item has plenty on hand but is fully committed to a different
        open Works Order — available_qty in the served JSON is reduced."""
        item = Item(code=self._next_code("NET-CM"), description="Committed Item",
                    category="Hardware", qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()

        # Demand from an unrelated open Works Order (not the one being edited).
        other_so = self._make_so(session)
        other_wo = self._make_open_wo(session, other_so)
        session.add(BOMLine(wo_id=other_wo.id, item_id=item.id, qty_required=90.0,
                            qty_issued=0.0, line_type="COMPONENT"))

        so = self._make_so(session)
        wo = self._make_open_wo(session, so)
        session.commit()

        catalogue = self._get_catalogue_items(client, wo.id)
        served = self._find_item(catalogue, item.code)

        assert served['qty_on_hand'] == 100.0
        assert served['qty_on_order'] == 0.0
        assert served['qty_committed'] == 90.0
        assert served['available_qty'] == 10.0  # 100 - 90

    def test_next_po_due_absent_when_no_open_po(self, app, db, session, client):
        """Item with no open/partial PO lines has next_po_due == null in the
        served JSON (not a truthy placeholder)."""
        item = Item(code=self._next_code("NET-NOPO"), description="No PO Item",
                    category="Hardware", qty_on_hand=10.0, active=True)
        session.add(item)
        session.flush()

        so = self._make_so(session)
        wo = self._make_open_wo(session, so)
        session.commit()

        catalogue = self._get_catalogue_items(client, wo.id)
        served = self._find_item(catalogue, item.code)

        assert served['next_po_due'] is None
        assert served['available_qty'] == 10.0
