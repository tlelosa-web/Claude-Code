"""Tests for bom_builder module."""
import pytest
from datetime import datetime
from models import db, Item, SalesOrder, WorksOrder, BOMLine

class TestBOMBuilder:
    _so_counter = 0
    
    @pytest.fixture
    def setup_data(self, app, db, session):
        """Set up test data with unique SO number and item codes."""
        TestBOMBuilder._so_counter += 1
        c = TestBOMBuilder._so_counter
        
        # Create sales order
        so = SalesOrder(so_number=f"SO-TEST-{c:03d}", reference="REF001", customer_name="Test Customer",
                        status='Draft', created_at=datetime.utcnow())
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
            item = Item.query.get(line.item_id)
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
        item = Item.query.get(bom_line.item_id)
        shortfall = max(0.0, bom_line.qty_required - item.qty_on_hand)
        assert shortfall == 8.0
    
    def test_total_cost_calculation(self, app, db, session, setup_data):
        """Test total cost calculation for BOM lines."""
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
        
        # Expected: (3 * 50.00) + (2 * 30.00) = 150 + 60 = 210
        assert context['total_excl_cost'] == 210.0
        assert len(context['lines']) == 2