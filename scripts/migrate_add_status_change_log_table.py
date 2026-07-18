"""Migration: Add status_change_log table.

Brand-new table (event-driven Change Log, docs/specs/
sales-order-report-excel-export-2026-07-17.md, Decision 2).
db.create_all() only creates tables that don't already exist, so this is
safe to run against a live DB that already has the other tables. Kept as
an explicit migration script per the project hard rule "no schema changes
without a migration file". No ensure_schema_columns() entry needed -- that
mechanism is for adding columns to existing tables, and db.create_all() on
every app startup already covers this brand-new table.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db


def add_status_change_log_table(app):
    """Idempotent core logic, factored out of migrate() so it can be
    exercised against a throwaway test app/DB without touching
    instance/sops.db (the CLI entry point below still targets the real
    app/DB via create_app())."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        if 'status_change_log' in existing_tables:
            print("OK status_change_log table already exists.")
            return

        db.create_all()  # only creates missing tables, leaves existing ones untouched
        print("OK Created status_change_log table.")


def migrate():
    add_status_change_log_table(create_app())


if __name__ == '__main__':
    migrate()
