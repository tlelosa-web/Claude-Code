"""Migration: Add SalesOrder.amount_paid column.

Needed so the SO detail page can capture a manually-typed Amount Paid figure
for the new 'Cash Sale - Partial' payment status and compute a Balance Due
(SalesOrder.total_incl - amount_paid).

See docs/specs/payment-status-cash-account-amount-paid.md.
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

        if 'sales_order' in inspector.get_table_names():
            columns = {c['name'] for c in inspector.get_columns('sales_order')}
            if 'amount_paid' not in columns:
                db.session.execute(text(
                    'ALTER TABLE sales_order ADD COLUMN amount_paid FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added amount_paid column to sales_order.")
            else:
                print("OK amount_paid column already exists on sales_order.")

if __name__ == '__main__':
    migrate()
