"""Regression tests for bug sweep Fix 4 — unguarded None arithmetic/
formatting on stock value and cost fields.

A legacy Item row with avg_cost/qty_on_hand=None (nullable per models.py;
Batch 19 removed the CSV-import path that used to backfill qty_on_hand on
every existing row, so a legacy NULL can persist indefinitely) must not
500 the Stock Report or Item catalogue AJAX endpoints.

Rows are inserted via Core `Item.__table__.insert()` rather than the ORM
constructor - the ORM applies the Column `default=0.0` even when None is
passed explicitly (SQLAlchemy can't tell "explicit None" from "omitted"
at the ORM layer), so a plain `Item(avg_cost=None)` silently becomes 0.0
and never exercises the guard. Core insert() honours an explicit None.

See docs/specs/bug-sweep-2026-07-14.md (Fix 4).
"""
from models import Item


class TestNoneGuardedStockAndCostFields:
    _c = 0

    def _next_code(self):
        TestNoneGuardedStockAndCostFields._c += 1
        return f"NONE-GUARD-{TestNoneGuardedStockAndCostFields._c:03d}"

    def test_stock_data_survives_null_avg_cost_and_qty_on_hand(self, app, db, session, client):
        session.execute(Item.__table__.insert().values(
            code=self._next_code(), description="Legacy item with NULL cost fields",
            qty_on_hand=None, avg_cost=None, active=True,
        ))
        session.commit()

        response = client.get('/reports/stock/data?active_only=false')
        assert response.status_code == 200

    def test_stock_export_csv_survives_null_avg_cost_and_qty_on_hand(self, app, db, session, client):
        session.execute(Item.__table__.insert().values(
            code=self._next_code(), description="Legacy item with NULL cost fields",
            qty_on_hand=None, avg_cost=None, active=True,
        ))
        session.commit()

        response = client.get('/reports/stock/export-csv')
        assert response.status_code == 200

    def test_items_ajax_survives_null_cost_and_price_fields(self, app, db, session, client):
        session.execute(Item.__table__.insert().values(
            code=self._next_code(), description="Legacy item with NULL cost/price fields",
            qty_on_hand=None, last_cost=None, avg_cost=None,
            excl_price=None, incl_price=None, active=True,
        ))
        session.commit()

        response = client.get('/items', headers={'X-Requested-With': 'XMLHttpRequest'})
        assert response.status_code == 200
