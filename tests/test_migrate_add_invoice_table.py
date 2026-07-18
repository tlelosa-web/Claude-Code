"""Tests for scripts/migrate_add_invoice_table.py.

Exercises the migration's core table-creation logic against a throwaway
in-memory SQLite DB -- never instance/sops.db.
"""
from flask import Flask

from models import db
from scripts.migrate_add_invoice_table import add_invoice_table


def _make_empty_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def test_creates_invoice_table_on_fresh_db():
    app = _make_empty_app()

    add_invoice_table(app)

    with app.app_context():
        inspector = db.inspect(db.engine)
        assert 'invoice' in inspector.get_table_names()


def test_invoice_table_columns_match_model():
    app = _make_empty_app()

    add_invoice_table(app)

    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = {c['name'] for c in inspector.get_columns('invoice')}
        assert columns == {
            'id', 'invoice_number', 'customer_ref', 'customer_name',
            'sales_rep', 'invoice_date', 'due_date', 'exclusive', 'vat',
            'total_selling', 'total_outstanding', 'imported_at',
        }


def test_idempotent_safe_to_run_twice():
    app = _make_empty_app()

    add_invoice_table(app)
    add_invoice_table(app)  # must not raise

    with app.app_context():
        inspector = db.inspect(db.engine)
        assert 'invoice' in inspector.get_table_names()
