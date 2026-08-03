"""Migration: Add Item.amu / Item.suggested_min / Item.suggested_max columns.

Needed for the AMU + suggested Min/Max reorder-level import (from Sage
ItemMovementReport.csv), which enriches existing catalogue items with an
average monthly usage figure and AMU-based suggested reorder levels.
0.0 means "not computed" on all three, same convention as
Item.reorder_point/max_level. Purely informational - never written into the
existing, manually-curated Item.reorder_point/max_level/reorder_qty fields.

See docs/specs/amu-minmax-reorder-suggestion-2026-07-17.md.
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
            if 'amu' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN amu FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added amu column to item.")
            else:
                print("OK amu column already exists on item.")

            if 'suggested_min' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN suggested_min FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added suggested_min column to item.")
            else:
                print("OK suggested_min column already exists on item.")

            if 'suggested_max' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN suggested_max FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added suggested_max column to item.")
            else:
                print("OK suggested_max column already exists on item.")

if __name__ == '__main__':
    migrate()
