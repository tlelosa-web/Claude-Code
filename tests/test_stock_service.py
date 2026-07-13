"""Tests for stock_service module."""
import pytest
from datetime import datetime, timezone
from models import db, Item, StockMovement

class TestStockService:
    
    def test_issue_deducts_qty(self, app, db, session):
        """Test that issue() deducts quantity on hand."""
        from services.stock_service import issue
        
        # Create test item
        item = Item(code="TEST001", description="Test Item", qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()
        
        # Issue 25 units
        issue(item.id, 25, "WO-TEST-001", "Test issue", "Tester")
        session.commit()
        
        # Verify
        item = db.session.get(Item, item.id)
        assert item.qty_on_hand == 75.0
        
        movement = StockMovement.query.filter_by(item_id=item.id, movement_type='ISSUE').first()
        assert movement is not None
        assert movement.qty_change == -25.0
        assert movement.qty_after == 75.0
        assert movement.reference == "WO-TEST-001"
    
    def test_receipt_adds_qty(self, app, db, session):
        """Test that receipt() adds quantity on hand."""
        from services.stock_service import receipt
        
        item = Item(code="TEST002", description="Test Item 2", qty_on_hand=50.0, active=True)
        session.add(item)
        session.flush()
        
        receipt(item.id, 30, "PO-TEST-001", "Test receipt", "Tester")
        session.commit()
        
        item = db.session.get(Item, item.id)
        assert item.qty_on_hand == 80.0
        
        movement = StockMovement.query.filter_by(item_id=item.id, movement_type='RECEIPT').first()
        assert movement is not None
        assert movement.qty_change == 30.0
        assert movement.qty_after == 80.0
    
    def test_adjustment_records_movement(self, app, db, session):
        """Test that adjust() changes qty and records movement."""
        from services.stock_service import adjust
        
        item = Item(code="TEST003", description="Test Item 3", qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()
        
        adjust(item.id, 120.0, "Cycle count correction", "Stock Clerk")
        session.commit()
        
        item = db.session.get(Item, item.id)
        assert item.qty_on_hand == 120.0
        
        movement = StockMovement.query.filter_by(item_id=item.id, movement_type='ADJUSTMENT').first()
        assert movement is not None
        assert movement.qty_change == 20.0  # 120 - 100
        assert movement.qty_after == 120.0
        assert movement.notes == "Cycle count correction"
        assert movement.created_by == "Stock Clerk"
    
    def test_reverse_issue_adds_qty_back(self, app, db, session):
        """Test that reverse_issue() adds qty back and logs a REVERSAL movement."""
        from services.stock_service import reverse_issue

        item = Item(code="TEST005", description="Test Item 5", qty_on_hand=50.0, active=True)
        session.add(item)
        session.flush()

        reverse_issue(item.id, 15, "WO-TEST-005", "Reversed on reopen", "Tester")
        session.commit()

        item = db.session.get(Item, item.id)
        assert item.qty_on_hand == 65.0

        movement = StockMovement.query.filter_by(item_id=item.id, movement_type='REVERSAL').first()
        assert movement is not None
        assert movement.qty_change == 15.0
        assert movement.qty_after == 65.0
        assert movement.reference == "WO-TEST-005"

    def test_qty_after_snapshot(self, app, db, session):
        """Test that qty_after correctly reflects state after movement."""
        from services.stock_service import issue, receipt
        
        item = Item(code="TEST004", description="Test Item 4", qty_on_hand=100.0, active=True)
        session.add(item)
        session.flush()
        
        # Issue 10
        issue(item.id, 10, "WO-001", "Issue 1", "Tester")
        session.flush()
        
        # Issue 20 more
        issue(item.id, 20, "WO-002", "Issue 2", "Tester")
        session.flush()
        
        # Check movements
        movements = StockMovement.query.filter_by(item_id=item.id).order_by(StockMovement.created_at).all()
        assert len(movements) == 2
        assert movements[0].qty_after == 90.0  # 100 - 10
        assert movements[1].qty_after == 70.0  # 90 - 20