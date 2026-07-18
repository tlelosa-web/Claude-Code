"""Tests for services/status_change_log.py -- log_change() and the
track_report_status() context manager. See docs/specs/
sales-order-report-excel-export-2026-07-17.md Decision 2.
"""
from datetime import datetime, timezone

from models import SalesOrder, SOLineItem, WorksOrder, StockOrder, StatusChangeLog


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


class TestBuildBomLogging:
    """build_bom() (routes/sales_orders.py) must, in one POST call, log both
    the SO's report_status Loaded->Released transition (via
    track_report_status()) and the new order's own initial status=Open
    creation event (via a direct log_change() call, old_value=None meaning
    'did not exist before')."""

    def test_build_bom_creates_wo_logs_report_status_and_wo_creation(self, client, db, session):
        # build_bom()'s sequential WO-numbering logic looks at the most
        # recently created WorksOrder row across the whole (session-scoped,
        # shared) test DB; other test files freely create WorksOrders with
        # non-"WO####" numbers, which would otherwise reset the counter to
        # 1 and risk a UNIQUE-constraint collision with an earlier test's
        # "WO0001". Anchor with a cleanly-parseable, high number first so
        # this test's own generated number is deterministic and collision-free.
        anchor_so = SalesOrder(so_number='SO-ANCHOR-WO-LOG', status='Cancelled',
                                created_at=datetime.now(timezone.utc))
        session.add(anchor_so)
        session.flush()
        session.add(WorksOrder(wo_number='WO9000', so_id=anchor_so.id,
                                order_type='ASSEMBLY', status='Cancelled'))
        session.commit()

        so = SalesOrder(so_number='SO-BUILDLOG-001', status='Draft',
                         created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        fan_line = SOLineItem(so_id=so.id, description="NO-MATCH-CODE - Fan Assembly", qty=1.0)
        session.add(fan_line)
        session.commit()

        assert so.report_status == 'Loaded'

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{fan_line.id}": "fan",
            f"line_job_number_{fan_line.id}": "FM8001",
            "issued_by": "Tester",
        })
        assert resp.status_code in (200, 302)

        wo = WorksOrder.query.filter_by(so_id=so.id).first()
        assert wo is not None

        so_rows = StatusChangeLog.query.filter_by(
            order_id=so.id, order_type='SO', field_name='report_status').all()
        assert len(so_rows) == 1
        assert so_rows[0].old_value == 'Loaded'
        assert so_rows[0].new_value == 'Released'

        wo_rows = StatusChangeLog.query.filter_by(
            order_id=wo.id, order_type='WO', field_name='status').all()
        assert len(wo_rows) == 1
        assert wo_rows[0].old_value is None
        assert wo_rows[0].new_value == 'Open'
        assert wo_rows[0].order_number == wo.wo_number

    def test_build_bom_creates_sto_logs_report_status_and_sto_creation(self, client, db, session):
        # Same collision-avoidance anchor as above, for StockOrder numbering.
        anchor_so = SalesOrder(so_number='SO-ANCHOR-STO-LOG', status='Cancelled',
                                created_at=datetime.now(timezone.utc))
        session.add(anchor_so)
        session.flush()
        session.add(StockOrder(stock_order_number='STO9000', so_id=anchor_so.id,
                                status='Cancelled'))
        session.commit()

        so = SalesOrder(so_number='SO-BUILDLOG-002', status='Draft',
                         created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()

        stock_line = SOLineItem(so_id=so.id, description="NO-MATCH-CODE - Spare Part", qty=1.0)
        session.add(stock_line)
        session.commit()

        assert so.report_status == 'Loaded'

        resp = client.post(f"/sales-orders/{so.id}/build-bom", data={
            f"line_role_{stock_line.id}": "stock",
        })
        assert resp.status_code == 302

        sto = StockOrder.query.filter_by(so_id=so.id).first()
        assert sto is not None

        so_rows = StatusChangeLog.query.filter_by(
            order_id=so.id, order_type='SO', field_name='report_status').all()
        assert len(so_rows) == 1
        assert so_rows[0].old_value == 'Loaded'
        assert so_rows[0].new_value == 'Released'

        sto_rows = StatusChangeLog.query.filter_by(
            order_id=sto.id, order_type='STO', field_name='status').all()
        assert len(sto_rows) == 1
        assert sto_rows[0].old_value is None
        assert sto_rows[0].new_value == 'Open'
        assert sto_rows[0].order_number == sto.stock_order_number
