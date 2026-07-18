"""Tests for editable Delivery Date and the `dmy` display filter.

See docs/specs/payment-status-delivery-date-reopen-columns.md (Part B).
"""
from datetime import date, datetime, timezone
from models import db, SalesOrder, StatusChangeLog


class TestUpdateDeliveryDate:
    _c = 0

    def _mk_so(self, session):
        TestUpdateDeliveryDate._c += 1
        n = TestUpdateDeliveryDate._c
        so = SalesOrder(so_number=f"DELDATE-SO-{n:03d}", customer_name="Delivery Date Test Co",
                        status="Draft", delivery_date=date(2026, 1, 1),
                        created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_update_delivery_date_valid(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/delivery-date", data={"delivery_date": "2026-08-15"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.delivery_date == date(2026, 8, 15)

    def test_update_delivery_date_rejects_blank(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/delivery-date", data={"delivery_date": ""},
                           follow_redirects=True)
        assert resp.status_code == 200

        unchanged = db.session.get(SalesOrder, so.id)
        assert unchanged.delivery_date == date(2026, 1, 1)

    def test_update_delivery_date_rejects_invalid_format(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/delivery-date", data={"delivery_date": "15/08/2026"},
                           follow_redirects=True)
        assert resp.status_code == 200

        unchanged = db.session.get(SalesOrder, so.id)
        assert unchanged.delivery_date == date(2026, 1, 1)

    def test_update_delivery_date_logs_change_only_when_value_differs(self, client, session):
        so = self._mk_so(session)  # delivery_date starts at date(2026, 1, 1)
        before_count = StatusChangeLog.query.count()

        # Same value submitted -- no log row, no-op
        client.post(f"/sales-orders/{so.id}/delivery-date", data={"delivery_date": "2026-01-01"})
        assert StatusChangeLog.query.count() == before_count

        # Different value -- exactly one log row
        client.post(f"/sales-orders/{so.id}/delivery-date", data={"delivery_date": "2026-08-15"})
        # old_value/new_value are Text columns -- SQLite coerces the date
        # objects to their ISO string form on storage (see
        # services/status_change_log.py module docstring).
        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO', field_name='delivery_date').all()
        assert len(rows) == 1
        assert rows[0].old_value == date(2026, 1, 1).isoformat()
        assert rows[0].new_value == date(2026, 8, 15).isoformat()

    def test_update_delivery_date_blank_rejection_writes_no_log_row(self, client, session):
        so = self._mk_so(session)
        before_count = StatusChangeLog.query.count()

        client.post(f"/sales-orders/{so.id}/delivery-date", data={"delivery_date": ""}, follow_redirects=True)

        assert StatusChangeLog.query.count() == before_count


class TestDmyFilter:
    def test_dmy_filter_formats_date_as_ddmmyyyy(self, app):
        dmy = app.jinja_env.filters['dmy']
        assert dmy(date(2026, 8, 15)) == '15/08/2026'

    def test_dmy_filter_blank_for_none(self, app):
        dmy = app.jinja_env.filters['dmy']
        assert dmy(None) == ''
