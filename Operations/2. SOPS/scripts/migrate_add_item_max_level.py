"""Migration: Add Item.max_level column.

Needed for the "Adjust Stock & Levels" modal (Item detail page), which adds
a target Max Level alongside the existing Reorder Point/Reorder Qty fields.
0.0 means "not set", same convention as Item.reorder_point.

See docs/specs/item-edit-and-levels-popup.md.
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
            if 'max_level' not in columns:
                db.session.execute(text(
                    'ALTER TABLE item ADD COLUMN max_level FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added max_level column to item.")
            else:
                print("OK max_level column already exists on item.")

if __name__ == '__main__':
    migrate()
