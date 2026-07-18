"""Tests for scripts/migrate_add_status_change_log_table.py.

Exercises the migration's core table-creation logic against a throwaway
in-memory SQLite DB -- never instance/sops.db.
"""
from flask import Flask

from models import db
from scripts.migrate_add_status_change_log_table import add_status_change_log_table


def _make_empty_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def test_creates_status_change_log_table_on_fresh_db():
    app = _make_empty_app()

    add_status_change_log_table(app)

    with app.app_context():
        inspector = db.inspect(db.engine)
        assert 'status_change_log' in inspector.get_table_names()


def test_status_change_log_table_columns_match_model():
    app = _make_empty_app()

    add_status_change_log_table(app)

    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = {c['name'] for c in inspector.get_columns('status_change_log')}
        assert columns == {
            'id', 'order_type', 'order_id', 'order_number', 'field_name',
            'old_value', 'new_value', 'changed_at', 'changed_by',
        }


def test_idempotent_safe_to_run_twice():
    app = _make_empty_app()

    add_status_change_log_table(app)
    add_status_change_log_table(app)  # must not raise

    with app.app_context():
        inspector = db.inspect(db.engine)
        assert 'status_change_log' in inspector.get_table_names()
