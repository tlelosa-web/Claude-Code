"""Migration: Add invoice table.

Brand-new table (native Sales Order Report Excel export, Monthly INV tab
source -- docs/specs/sales-order-report-excel-export-2026-07-17.md,
Decision 4). db.create_all() only creates tables that don't already exist,
so this is safe to run against a live DB that already has the other
tables. Kept as an explicit migration script per the project hard rule
"no schema changes without a migration file".
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db


def add_invoice_table(app):
    """Idempotent core logic, factored out of migrate() so it can be
    exercised against a throwaway test app/DB without touching
    instance/sops.db (the CLI entry point below still targets the real
    app/DB via create_app())."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        if 'invoice' in existing_tables:
            print("OK invoice table already exists.")
            return

        db.create_all()  # only creates missing tables, leaves existing ones untouched
        print("OK Created invoice table.")


def migrate():
    add_invoice_table(create_app())


if __name__ == '__main__':
    migrate()
