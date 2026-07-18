"""Tests for services/status_change_log.py -- log_change() and the
track_report_status() context manager. See docs/specs/
sales-order-report-excel-export-2026-07-17.md Decision 2.
"""
from models import SalesOrder, WorksOrder, StatusChangeLog


class TestLogChange:

    def test_writes_correct_row(self, app, db, session):
        from services.status_change_log import log_change

        so = SalesOrder(so_number='SO-LOG-001', status='Open')
        session.add(so)
        session.commit()

        log_change('SO', so.id, so.so_number, 'payment_status',
                    'Account - Pending', 'Account - Up to Date', changed_by='Tester')
        session.commit()

        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO').all()
        assert len(rows) == 1
        row = rows[0]
        assert row.order_number == 'SO-LOG-001'
        assert row.field_name == 'payment_status'
        assert row.old_value == 'Account - Pending'
        assert row.new_value == 'Account - Up to Date'
        assert row.changed_by == 'Tester'


class TestTrackReportStatus:

    def test_no_op_block_writes_nothing(self, app, db, session):
        """Wrapping a block that doesn't actually change report_status must
        not write any StatusChangeLog row."""
        from services.status_change_log import track_report_status

        so = SalesOrder(so_number='SO-TRACK-001', status='Open')
        session.add(so)
        session.commit()

        before_count = StatusChangeLog.query.count()

        with track_report_status(so):
            pass  # no-op -- report_status stays 'Loaded' throughout

        session.commit()

        assert StatusChangeLog.query.count() == before_count

    def test_creating_wo_logs_loaded_to_released(self, app, db, session):
        """Wrapping a block that creates a WorksOrder (so report_status goes
        Loaded -> Released) must write exactly one row with the correct
        old/new values."""
        from services.status_change_log import track_report_status

        so = SalesOrder(so_number='SO-TRACK-002', status='Draft')
        session.add(so)
        session.commit()

        assert so.report_status == 'Loaded'

        with track_report_status(so):
            wo = WorksOrder(wo_number='WO-TRACK-002', so_id=so.id,
                             order_type='ASSEMBLY', status='Open')
            session.add(wo)
            session.flush()

        session.commit()

        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO',
                                                 field_name='report_status').all()
        assert len(rows) == 1
        assert rows[0].old_value == 'Loaded'
        assert rows[0].new_value == 'Released'
