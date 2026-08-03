"""Event-driven audit log helpers for the fixed tracked-field list described
in docs/specs/sales-order-report-excel-export-2026-07-17.md Decision 2.

`log_change()` is a thin, direct DB-write helper for fields with a real
before/after value at the call site (WO.status, STO.status, on_hold,
payment_status, amount_paid, delivery_date, report_notes).

`track_report_status()` is the reusable primitive for the one field with no
setter to intercept -- SalesOrder.report_status is a computed property, so
callers wrap whatever WO/STO/SO mutation is already happening and let this
context manager diff the computed value before/after, writing a log row
only if it actually changed.
"""
from contextlib import contextmanager

from models import db, StatusChangeLog


def log_change(order_type, order_id, order_number, field_name, old_value, new_value, changed_by=None):
    """Write one StatusChangeLog row. Values are stored as-is (Text columns);
    callers pass whatever str()-able value is meaningful for that field."""
    entry = StatusChangeLog(
        order_type=order_type,
        order_id=order_id,
        order_number=order_number,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by,
    )
    db.session.add(entry)
    return entry


@contextmanager
def track_report_status(so, changed_by=None):
    """Wrap a block of code that may change `so.report_status` (e.g.
    build_bom() creating a WO/STO, or a WO/STO status flip elsewhere).
    Captures the computed report_status before the block runs, lets the
    block run, then logs a single StatusChangeLog row only if the computed
    value actually changed -- a no-op (no row written) otherwise."""
    before = so.report_status
    yield
    # `report_status` is derived from the `works_orders`/`stock_orders`
    # relationship collections, which SQLAlchemy caches in-memory after
    # first access (e.g. the `before` read above). A WO/STO created inside
    # the wrapped block sets its FK column directly (matching build_bom()'s
    # own pattern), which does not retroactively update an already-cached
    # collection -- expire it so `after` reflects the current DB state
    # (autoflush covers any pending, not-yet-committed writes).
    db.session.expire(so, ['works_orders', 'stock_orders'])
    after = so.report_status
    if before != after:
        log_change('SO', so.id, so.so_number, 'report_status', before, after, changed_by=changed_by)
