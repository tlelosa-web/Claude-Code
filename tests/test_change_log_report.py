"""Tests for the Change Log report (routes/reports.py change_log() /
change_log_data()) -- see docs/specs/
sales-order-report-excel-export-2026-07-17.md Decision 2, Sequencing 21-23.
"""
from datetime import datetime, timezone

from models import SalesOrder, StatusChangeLog
from services.status_change_log import log_change


class TestChangeLogReport:
    _c = 0

    def _mk_so(self, session):
        TestChangeLogReport._c += 1
        n = TestChangeLogReport._c
        so = SalesOrder(so_number=f"CHGLOG-SO-{n:03d}", customer_name="Change Log Test Co",
                        status="Draft", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_change_log_page_renders(self, client):
        resp = client.get('/reports/change-log')
        assert resp.status_code == 200

    def test_data_route_returns_seeded_rows(self, client, session):
        so = self._mk_so(session)
        log_change('SO', so.id, so.so_number, 'payment_status',
                   'Account - Pending', 'Account - Up to Date', changed_by='Tester')
        log_change('WO', 9001, 'WO-CHGLOG-001', 'status', 'Open', 'Released', changed_by='Tester')
        session.commit()

        resp = client.get('/reports/change-log/data')
        assert resp.status_code == 200
        data = resp.get_json()

        order_numbers = [c['order_number'] for c in data['changes']]
        assert so.so_number in order_numbers
        assert 'WO-CHGLOG-001' in order_numbers

    def test_date_range_filter_narrows_correctly(self, client, session):
        so = self._mk_so(session)

        entry = log_change('SO', so.id, so.so_number, 'on_hold', False, True, changed_by='Tester')
        session.commit()
        entry.changed_at = datetime(2020, 1, 1, 12, 0, 0)
        session.commit()

        # A date range that excludes 2020-01-01 must not return this row.
        resp = client.get('/reports/change-log/data?date_from=2099-01-01&date_to=2099-12-31')
        data = resp.get_json()
        assert entry.id not in [None]  # sanity -- entry persisted
        assert not any(c['order_number'] == so.so_number and c['field_name'] == 'on_hold'
                       for c in data['changes'])

        # A date range that includes 2020-01-01 must return it.
        resp = client.get('/reports/change-log/data?date_from=2019-12-01&date_to=2020-02-01')
        data = resp.get_json()
        assert any(c['order_number'] == so.so_number and c['field_name'] == 'on_hold'
                   for c in data['changes'])

    def test_order_type_filter_narrows_correctly(self, client, session):
        so = self._mk_so(session)
        log_change('SO', so.id, so.so_number, 'amount_paid', 0.0, 100.0, changed_by='Tester')
        log_change('STO', 9002, 'STO-CHGLOG-001', 'status', 'Open', 'Released', changed_by='Tester')
        session.commit()

        resp = client.get('/reports/change-log/data?order_type=STO')
        data = resp.get_json()
        assert all(c['order_type'] == 'STO' for c in data['changes'])
        assert any(c['order_number'] == 'STO-CHGLOG-001' for c in data['changes'])
        assert not any(c['order_number'] == so.so_number for c in data['changes'])

        resp = client.get('/reports/change-log/data?order_type=SO')
        data = resp.get_json()
        assert all(c['order_type'] == 'SO' for c in data['changes'])
        assert any(c['order_number'] == so.so_number for c in data['changes'])

    def test_field_name_filter_narrows_correctly(self, client, session):
        so = self._mk_so(session)
        log_change('SO', so.id, so.so_number, 'delivery_date', '2026-01-01', '2026-08-15', changed_by='Tester')
        log_change('SO', so.id, so.so_number, 'report_notes', 'old note', 'new note', changed_by='Tester')
        session.commit()

        resp = client.get('/reports/change-log/data?field_name=report_notes')
        data = resp.get_json()
        assert all(c['field_name'] == 'report_notes' for c in data['changes'])
        assert any(c['order_number'] == so.so_number and c['new_value'] == 'new note'
                   for c in data['changes'])
        assert not any(c['field_name'] == 'delivery_date' for c in data['changes'])

    def test_full_row_snapshot_fields_never_appear_as_field_name(self, client, session):
        # customer_name is a real SalesOrder column that changes routinely
        # (e.g. via save_order() PDF re-upload) but is deliberately never
        # logged by this feature -- StatusChangeLog only ever gets rows for
        # the fixed tracked-field list. Mutating it directly (bypassing any
        # route) proves no code path anywhere writes a StatusChangeLog row
        # for it.
        so = self._mk_so(session)
        so.customer_name = "Renamed Customer"
        session.commit()

        # Also seed one real tracked-field change so the log isn't empty.
        log_change('SO', so.id, so.so_number, 'payment_status', 'Account - Pending',
                   'Account - Up to Date', changed_by='Tester')
        session.commit()

        resp = client.get('/reports/change-log/data')
        data = resp.get_json()
        field_names = {c['field_name'] for c in data['changes']}

        assert 'customer_name' not in field_names

        # Explicitly filtering by a non-tracked field name must return
        # nothing rather than erroring.
        resp = client.get('/reports/change-log/data?field_name=customer_name')
        data = resp.get_json()
        assert data['changes'] == []

        # And the row count in the DB directly confirms no StatusChangeLog
        # row was ever written for the customer_name mutation above.
        assert StatusChangeLog.query.filter_by(field_name='customer_name').count() == 0
