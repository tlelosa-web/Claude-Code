"""Migration: Add setting table + seed default currency_symbol row.

Brand-new table (Settings module, docs/specs/po-price-date-columns-
currency-settings-2026-07-16.md, Part C). db.create_all() only creates
tables that don't already exist, so this is safe to run against a live DB
that already has the other tables. Kept as an explicit migration script
per the project hard rule "no schema changes without a migration file".

Also seeds ('currency_symbol', 'R') if that key doesn't already exist, so
display is unchanged until the setting is edited via /settings.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, Setting


def migrate():
    app = create_app()
    with app.app_context():
        inspector = db.inspect(db.engine)

        if 'setting' not in inspector.get_table_names():
            db.create_all()  # only creates missing tables, leaves existing ones untouched
            print("OK Created setting table.")
        else:
            print("OK setting table already exists.")

        if not Setting.query.filter_by(key='currency_symbol').first():
            db.session.add(Setting(key='currency_symbol', value='R'))
            db.session.commit()
            print("OK Seeded currency_symbol = 'R'.")
        else:
            print("OK currency_symbol setting already seeded.")


if __name__ == '__main__':
    migrate()
