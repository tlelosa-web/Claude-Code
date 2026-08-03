"""Migration: Add job_number column to so_line_item table."""
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
        if 'so_line_item' not in inspector.get_table_names():
            print("Table so_line_item does not exist — nothing to migrate.")
            return
        
        columns = {c['name'] for c in inspector.get_columns('so_line_item')}
        if 'job_number' not in columns:
            db.session.execute(text(
                'ALTER TABLE so_line_item ADD COLUMN job_number VARCHAR(50)'
            ))
            db.session.commit()
            print("OK Added job_number column to so_line_item.")
        else:
            print("OK job_number column already exists.")

if __name__ == '__main__':
    migrate()