"""Migration: Add StockOrderLine.qty_issued column.

Needed so completing a Stock Order can deduct stock per line (mirroring
BOMLine.qty_issued), and so Reopen knows precisely how much to reverse.

See docs/specs/payment-status-delivery-date-reopen-columns.md (Part C0).
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

        if 'stock_order_line' in inspector.get_table_names():
            columns = {c['name'] for c in inspector.get_columns('stock_order_line')}
            if 'qty_issued' not in columns:
                db.session.execute(text(
                    'ALTER TABLE stock_order_line ADD COLUMN qty_issued FLOAT DEFAULT 0.0'
                ))
                db.session.commit()
                print("OK Added qty_issued column to stock_order_line.")
            else:
                print("OK qty_issued column already exists on stock_order_line.")

if __name__ == '__main__':
    migrate()
