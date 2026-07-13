"""Tests for item_importer module."""
import pytest
import os
import tempfile
import csv
from models import db, Item, StockMovement

class TestItemImporter:
    
    def _create_test_csv(self, tmp_path, rows):
        """Helper to create a test CSV with sep=, header."""
        filepath = os.path.join(tmp_path, 'test_items.csv')
        with open(filepath, 'w', newline='') as f:
            f.write('sep=,\n')
            writer = csv.DictWriter(f, fieldnames=[
                'Code', 'Description', 'Category', 'Last Cost', 'Avg. Cost',
                'Excl. Price', 'Incl. Price', 'Qty on Hand', 'Active'
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return filepath
    
    def test_import_inserts_new(self, app, db, session, tmp_path):
        """Test that import inserts new items correctly."""
        from services.item_importer import import_items_from_csv
        
        rows = [
            {'Code': 'NEW-001', 'Description': 'New Item 1', 'Category': 'Test',
             'Last Cost': 'R 100.00', 'Avg. Cost': 'R 95.00', 'Excl. Price': 'R 150.00',
             'Incl. Price': 'R 172.50', 'Qty on Hand': '50', 'Active': 'Yes'},
            {'Code': 'NEW-002', 'Description': 'New Item 2', 'Category': 'Test',
             'Last Cost': 'R 200.00', 'Avg. Cost': 'R 190.00', 'Excl. Price': 'R 300.00',
             'Incl. Price': 'R 345.00', 'Qty on Hand': '25', 'Active': 'Yes'},
        ]
        
        filepath = self._create_test_csv(tmp_path, rows)
        updated, inserted, skipped = import_items_from_csv(filepath)
        
        assert inserted == 2
        assert updated == 0
        assert skipped == 0
        
        # Verify items in DB
        item1 = Item.query.filter_by(code='NEW-001').first()
        assert item1 is not None
        assert item1.description == 'New Item 1'
        assert item1.category == 'Test'
        assert item1.qty_on_hand == 50.0
        assert item1.last_cost == 100.0
        assert item1.avg_cost == 95.0
        
        # Check OPENING movement was created
        movement = StockMovement.query.filter_by(item_id=item1.id, movement_type='OPENING').first()
        assert movement is not None
        assert movement.qty_change == 50.0
    
    def test_import_updates_existing(self, app, db, session, tmp_path):
        """Test that import updates existing items (matched by code), but
        never touches qty_on_hand — SOPS owns the stock lifecycle, not CSV."""
        from services.item_importer import import_items_from_csv

        # Pre-insert an item
        existing = Item(code='EXIST-001', description='Old Description', category='Old',
                       qty_on_hand=10.0, last_cost=50.0, avg_cost=45.0, active=True)
        session.add(existing)
        session.commit()

        rows = [
            {'Code': 'EXIST-001', 'Description': 'Updated Description', 'Category': 'Updated',
             'Last Cost': 'R 75.00', 'Avg. Cost': 'R 70.00', 'Excl. Price': 'R 120.00',
             'Incl. Price': 'R 138.00', 'Qty on Hand': '20', 'Active': 'Yes'},
        ]

        filepath = self._create_test_csv(tmp_path, rows)
        updated, inserted, skipped = import_items_from_csv(filepath)

        assert inserted == 0
        assert updated == 1
        assert skipped == 0

        # Verify item's metadata was updated but qty_on_hand was preserved
        item = Item.query.filter_by(code='EXIST-001').first()
        assert item.description == 'Updated Description'
        assert item.category == 'Updated'
        assert item.qty_on_hand == 10.0
        assert item.last_cost == 75.0

    def test_import_preserves_qty_on_hand_when_csv_differs(self, app, db, session, tmp_path):
        """Regression test: an existing item's qty_on_hand must remain
        unchanged after import, even when the CSV row shows a different
        quantity for that code."""
        from services.item_importer import import_items_from_csv

        existing = Item(code='PRESERVE-001', description='Widget', category='Test',
                       qty_on_hand=42.0, last_cost=10.0, avg_cost=9.0, active=True)
        session.add(existing)
        session.commit()

        rows = [
            {'Code': 'PRESERVE-001', 'Description': 'Widget', 'Category': 'Test',
             'Last Cost': 'R 10.00', 'Avg. Cost': 'R 9.00', 'Excl. Price': 'R 15.00',
             'Incl. Price': 'R 17.25', 'Qty on Hand': '999', 'Active': 'Yes'},
        ]

        filepath = self._create_test_csv(tmp_path, rows)
        updated, inserted, skipped = import_items_from_csv(filepath)

        assert updated == 1
        assert inserted == 0

        item = Item.query.filter_by(code='PRESERVE-001').first()
        assert item.qty_on_hand == 42.0
    
    def test_import_skips_inactive(self, app, db, session, tmp_path):
        """Test that inactive items (Active != 'Yes') are skipped."""
        from services.item_importer import import_items_from_csv
        
        rows = [
            {'Code': 'INACTIVE-001', 'Description': 'Inactive Item', 'Category': 'Test',
             'Last Cost': 'R 0.00', 'Avg. Cost': 'R 0.00', 'Excl. Price': 'R 0.00',
             'Incl. Price': 'R 0.00', 'Qty on Hand': '0', 'Active': 'No'},
        ]
        
        filepath = self._create_test_csv(tmp_path, rows)
        updated, inserted, skipped = import_items_from_csv(filepath)
        
        assert inserted == 0
        assert skipped == 1
        
        # Verify item not in DB
        item = Item.query.filter_by(code='INACTIVE-001').first()
        assert item is None
    
    def test_import_handles_currency_format(self, app, db, session, tmp_path):
        """Test that 'R 1,500.00' format is correctly parsed as float."""
        from services.item_importer import import_items_from_csv
        
        rows = [
            {'Code': 'CURR-001', 'Description': 'Currency Test', 'Category': 'Test',
             'Last Cost': 'R 1,500.00', 'Avg. Cost': 'R 1,450.50', 'Excl. Price': 'R 2,199.99',
             'Incl. Price': 'R 2,529.99', 'Qty on Hand': '100', 'Active': 'Yes'},
        ]
        
        filepath = self._create_test_csv(tmp_path, rows)
        updated, inserted, skipped = import_items_from_csv(filepath)
        
        assert inserted == 1
        
        item = Item.query.filter_by(code='CURR-001').first()
        assert item.last_cost == 1500.00
        assert item.avg_cost == 1450.50
        assert item.excl_price == 2199.99
        assert item.incl_price == 2529.99