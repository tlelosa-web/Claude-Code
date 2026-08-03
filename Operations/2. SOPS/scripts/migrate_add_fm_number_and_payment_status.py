"""Migration: Add WorksOrder.job_number, StockOrderLine.job_number,
SalesOrder.payment_status columns.

See docs/specs/fm-numbers-default-open-so-report.md.
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

        if 'works_order' in inspector.get_table_names():
            columns = {c['name'] for c in inspector.get_columns('works_order')}
            if 'job_number' not in columns:
                db.session.execute(text(
                    'ALTER TABLE works_order ADD COLUMN job_number VARCHAR(50)'
                ))
                db.session.commit()
                print("OK Added job_number column to works_order.")
            else:
                print("OK job_number column already exists on works_order.")

        if 'stock_order_line' in inspector.get_table_names():
            columns = {c['name'] for c in inspector.get_columns('stock_order_line')}
            if 'job_number' not in columns:
                db.session.execute(text(
                    'ALTER TABLE stock_order_line ADD COLUMN job_number VARCHAR(50)'
                ))
                db.session.commit()
                print("OK Added job_number column to stock_order_line.")
            else:
                print("OK job_number column already exists on stock_order_line.")

        if 'sales_order' in inspector.get_table_names():
            columns = {c['name'] for c in inspector.get_columns('sales_order')}
            if 'payment_status' not in columns:
                db.session.execute(text(
                    "ALTER TABLE sales_order ADD COLUMN payment_status VARCHAR(50) DEFAULT 'Pending'"
                ))
                db.session.commit()
                print("OK Added payment_status column to sales_order.")
            else:
                print("OK payment_status column already exists on sales_order.")

if __name__ == '__main__':
    migrate()
