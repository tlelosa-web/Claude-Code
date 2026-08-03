"""Migration: Add reorder_point and reorder_qty columns to item table.

Enhancement 2 - reorder point / min-max replenishment signals
(docs/specs/purchase-order-module-plan.md section 6). Both default to 0.0,
which is treated as "no reorder point set" (never flagged) so this is safe
to run against a live DB without changing any existing behavior until a
user explicitly sets values on individual items.
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
        if 'item' not in inspector.get_table_names():
            print("Table item does not exist - nothing to migrate.")
            return

        columns = {c['name'] for c in inspector.get_columns('item')}

        if 'reorder_point' not in columns:
            db.session.execute(text(
                'ALTER TABLE item ADD COLUMN reorder_point FLOAT DEFAULT 0.0'
            ))
            db.session.commit()
            print("OK Added reorder_point column to item.")
        else:
            print("OK reorder_point column already exists.")

        if 'reorder_qty' not in columns:
            db.session.execute(text(
                'ALTER TABLE item ADD COLUMN reorder_qty FLOAT DEFAULT 0.0'
            ))
            db.session.commit()
            print("OK Added reorder_qty column to item.")
        else:
            print("OK reorder_qty column already exists.")


if __name__ == '__main__':
    migrate()
