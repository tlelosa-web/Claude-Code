"""Migration: Add Item.is_stocked_finished_good column.

Opt-in flag for catalogue items that are real stocked/sellable finished
goods. When set, completing a Works Order for that assembly item credits
qty_on_hand via a PRODUCTION stock movement (reversed on reopen).
Defaults to False for every existing item — Tebello flags items manually.

See docs/specs/production-receipt-on-wo-complete.md.
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
            if 'is_stocked_finished_good' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN is_stocked_finished_good BOOLEAN DEFAULT 0'
                ))
                db.session.commit()
                print("OK Added is_stocked_finished_good column to item.")
            else:
                print("OK is_stocked_finished_good column already exists on item.")

if __name__ == '__main__':
    migrate()
