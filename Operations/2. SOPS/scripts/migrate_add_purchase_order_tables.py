"""Migration: Add purchase_order and po_line tables.

These are brand-new tables (Enhancement 1 - Purchase Order module,
docs/specs/purchase-order-module-plan.md). db.create_all() only creates
tables that don't already exist, so this is safe to run against a live DB
that already has the other 8 tables. Kept as an explicit migration script
per the project hard rule "no schema changes without a migration file".
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db


def migrate():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        if 'purchase_order' in existing_tables and 'po_line' in existing_tables:
            print("OK purchase_order and po_line tables already exist.")
            return

        db.create_all()  # only creates missing tables, leaves existing ones untouched
        print("OK Created purchase_order and po_line tables.")


if __name__ == '__main__':
    migrate()
