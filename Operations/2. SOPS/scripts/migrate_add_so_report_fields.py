"""Migration: Add SalesOrder.report_notes / on_hold / on_hold_reason columns.

Needed for the native Sales Order Report Excel export -- report_notes is a
manual, carried-forward Notes column for the export; on_hold/on_hold_reason
back the SO-level On Hold flag overlaid onto the computed report_status
(display_report_status). No total_override column -- dropped entirely per
Decision 3 (see spec below); report_status was never a stored column.

See docs/specs/sales-order-report-excel-export-2026-07-17.md
(section: "Schema changes -- migration plan").
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db
from sqlalchemy import text


def add_so_report_fields(app):
    """Idempotent core logic, factored out of migrate() so it can be
    exercised against a throwaway test app/DB without touching
    instance/sops.db (the CLI entry point below still targets the real
    app/DB via create_app())."""
    with app.app_context():
        inspector = db.inspect(db.engine)

        if 'sales_order' not in inspector.get_table_names():
            return

        columns = {c['name'] for c in inspector.get_columns('sales_order')}
        if 'report_notes' not in columns:
            db.session.execute(text(
                'ALTER TABLE sales_order ADD COLUMN report_notes TEXT'
            ))
            db.session.commit()
            print("OK Added report_notes column to sales_order.")
        else:
            print("OK report_notes column already exists on sales_order.")

        if 'on_hold' not in columns:
            db.session.execute(text(
                'ALTER TABLE sales_order ADD COLUMN on_hold BOOLEAN DEFAULT 0'
            ))
            db.session.commit()
            print("OK Added on_hold column to sales_order.")
        else:
            print("OK on_hold column already exists on sales_order.")

        if 'on_hold_reason' not in columns:
            db.session.execute(text(
                'ALTER TABLE sales_order ADD COLUMN on_hold_reason TEXT'
            ))
            db.session.commit()
            print("OK Added on_hold_reason column to sales_order.")
        else:
            print("OK on_hold_reason column already exists on sales_order.")


def migrate():
    add_so_report_fields(create_app())


if __name__ == '__main__':
    migrate()
