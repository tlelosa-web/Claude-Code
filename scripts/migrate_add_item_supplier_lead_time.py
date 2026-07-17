"""Migration: Add Item.supplier / Item.lead_time_weeks columns.

Needed for the Supplier + Lead Time import (from Sage
OutstandingPOByItemReport.csv), which enriches existing catalogue items
with their most-frequent supplier and average lead time in weeks.
0.0 means "not set" on lead_time_weeks, same convention as
Item.reorder_point/max_level. supplier is nullable, same convention as
Item.category.

See docs/specs/supplier-lead-time-import-2026-07-17.md.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)

        if 'item' in inspector.get_table_names():
            columns = {c['name'] for c in inspector.get_columns('item')}
            if 'supplier' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN supplier VARCHAR(255)'
                ))
                db.session.commit()
                print("OK Added supplier column to item.")
            else:
                print("OK supplier column already exists on item.")

            if 'lead_time_weeks' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN lead_time_weeks FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added lead_time_weeks column to item.")
            else:
                print("OK lead_time_weeks column already exists on item.")

if __name__ == '__main__':
    migrate()
