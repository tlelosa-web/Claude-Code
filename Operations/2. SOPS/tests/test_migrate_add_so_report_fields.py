"""Tests for scripts/migrate_add_so_report_fields.py.

Exercises the migration's core column-adding logic against a throwaway
in-memory SQLite DB -- never instance/sops.db. Builds its own minimal Flask
app (rather than app.create_app(), whose db.create_all() would already
include the new columns from the current models.py) so the "old" sales_order
table genuinely lacks report_notes/on_hold/on_hold_reason before the
migration runs.
"""
from flask import Flask
from sqlalchemy import text

from models import db
from scripts.migrate_add_so_report_fields import add_so_report_fields


def _make_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def _create_old_sales_order_table(app):
    """Bare-bones pre-migration sales_order table -- no report_notes/
    on_hold/on_hold_reason columns."""
    with app.app_context():
        db.session.execute(text(
            'CREATE TABLE sales_order ('
            'id INTEGER PRIMARY KEY, '
            'so_number VARCHAR(100), '
            "status VARCHAR(50) DEFAULT 'Draft'"
            ')'
        ))
        db.session.commit()


def _columns(app):
    with app.app_context():
        inspector = db.inspect(db.engine)
        return {c['name'] for c in inspector.get_columns('sales_order')}


def test_adds_all_three_columns_to_existing_table():
    app = _make_app()
    _create_old_sales_order_table(app)
    assert 'report_notes' not in _columns(app)

    add_so_report_fields(app)

    columns = _columns(app)
    assert {'report_notes', 'on_hold', 'on_hold_reason'} <= columns


def test_idempotent_safe_to_run_twice():
    app = _make_app()
    _create_old_sales_order_table(app)

    add_so_report_fields(app)
    add_so_report_fields(app)  # must not raise (duplicate ADD COLUMN)

    columns = _columns(app)
    assert {'report_notes', 'on_hold', 'on_hold_reason'} <= columns


def test_no_op_when_sales_order_table_missing():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # No sales_order table created at all -- must not raise.
    add_so_report_fields(app)
