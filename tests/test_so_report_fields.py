"""Tests for the Sales Order report-parity fields: SalesOrder.total_incl,
SalesOrder.payment_status (+ its update route), and StockOrder.job_numbers.

See docs/specs/fm-numbers-default-open-so-report.md.
"""
import pytest
from datetime import datetime, timezone
from models import db, SalesOrder, SOLineItem, StockOrder, StockOrderLine, WorksOrder, StatusChangeLog, PAYMENT_STATUS_OPTIONS
from scripts.migrate_payment_status_values import migrate_payment_status_values


class TestSalesOrderTotalIncl:
    _c = 0

    def _mk_so(self, session):
        TestSalesOrderTotalIncl._c += 1
        n = TestSalesOrderTotalIncl._c
        so = SalesOrder(so_number=f"REPORT-SO-{n:03d}", customer_name="Report Test Co",
                        status="Draft", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        return so

    def test_total_incl_sums_line_items(self, session):
        so = self._mk_so(session)
        session.add_all([
            SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=1000.0),
            SOLineItem(so_id=so.id, description="Line 2", qty=1.0, incl_total=500.5),
        ])
        session.commit()

        assert so.total_incl == 1500.5

    def test_total_incl_zero_with_no_lines(self, session):
        so = self._mk_so(session)
        session.commit()
        assert so.total_incl == 0

    def test_total_incl_ignores_none_values(self, session):
        so = self._mk_so(session)
        session.add(SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=None))
        session.commit()
        assert so.total_incl == 0


class TestPaymentStatus:
    _c = 0

    def _mk_so(self, session):
        TestPaymentStatus._c += 1
        n = TestPaymentStatus._c
        so = SalesOrder(so_number=f"REPORT-PAY-{n:03d}", customer_name="Report Test Co",
                        status="Draft", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_default_payment_status_is_account_pending(self, session):
        so = self._mk_so(session)
        assert so.payment_status == "Account - Pending"

    def test_update_payment_status_valid(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/payment-status", data={"payment_status": "Cash Sale - Paid"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Cash Sale - Paid"

    def test_update_payment_status_rejects_invalid_value(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/payment-status",
                           data={"payment_status": "Not A Real Status"}, follow_redirects=True)
        assert resp.status_code == 200

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Account - Pending"

    def test_all_options_are_settable(self, client, session):
        so = self._mk_so(session)
        for option in PAYMENT_STATUS_OPTIONS:
            resp = client.post(f"/sales-orders/{so.id}/payment-status", data={"payment_status": option})
            assert resp.status_code == 302
            updated = db.session.get(SalesOrder, so.id)
            assert updated.payment_status == option

    def test_options_list_is_exactly_the_seven_new_values_in_order(self):
        assert PAYMENT_STATUS_OPTIONS == (
            'Cash Sale - Unpaid', 'Cash Sale - Paid', 'Cash Sale - Partial',
            'Account - Pending', 'Account - Up to Date', 'Account - On Hold', 'Account - Overdue',
        )

    def test_old_bare_option_values_are_not_present(self):
        # 'Account - Up to Date' is intentionally excluded here -- it is a
        # direct match, unchanged, between the old and new lists.
        old_bare_values = {'Pending', 'Paid', 'Partially Paid', 'Unpaid', 'On Hold'}
        assert not (old_bare_values & set(PAYMENT_STATUS_OPTIONS))

    def test_update_payment_status_cash_sale_partial_persists_amount_paid(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/payment-status",
                           data={"payment_status": "Cash Sale - Partial", "amount_paid": "250.50"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Cash Sale - Partial"
        assert updated.amount_paid == 250.50

    def test_update_payment_status_rejects_non_numeric_amount_paid(self, client, session):
        so = self._mk_so(session)
        so.payment_status = "Account - Pending"
        so.amount_paid = 10.0
        session.commit()

        resp = client.post(f"/sales-orders/{so.id}/payment-status",
                           data={"payment_status": "Cash Sale - Partial", "amount_paid": "not-a-number"},
                           follow_redirects=True)
        assert resp.status_code == 200

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Account - Pending"
        assert updated.amount_paid == 10.0

    def test_update_payment_status_non_partial_ignores_submitted_amount_paid(self, client, session):
        so = self._mk_so(session)
        so.amount_paid = 42.0
        session.commit()

        resp = client.post(f"/sales-orders/{so.id}/payment-status",
                           data={"payment_status": "Account - Up to Date", "amount_paid": "999"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.payment_status == "Account - Up to Date"
        assert updated.amount_paid == 42.0

    def test_update_payment_status_logs_change_only_when_value_differs(self, client, session):
        so = self._mk_so(session)
        so.payment_status = "Account - Pending"
        session.commit()
        before_count = StatusChangeLog.query.count()

        # Same value submitted -- no log row, no-op
        client.post(f"/sales-orders/{so.id}/payment-status", data={"payment_status": "Account - Pending"})
        assert StatusChangeLog.query.count() == before_count

        # Different value -- exactly one payment_status log row
        client.post(f"/sales-orders/{so.id}/payment-status", data={"payment_status": "Cash Sale - Paid"})
        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO', field_name='payment_status').all()
        assert len(rows) == 1
        assert rows[0].old_value == "Account - Pending"
        assert rows[0].new_value == "Cash Sale - Paid"

    def test_update_payment_status_cash_sale_partial_logs_both_fields_as_separate_rows(self, client, session):
        so = self._mk_so(session)
        so.payment_status = "Account - Pending"
        so.amount_paid = 0.0
        session.commit()

        client.post(f"/sales-orders/{so.id}/payment-status",
                   data={"payment_status": "Cash Sale - Partial", "amount_paid": "250.50"})

        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO').all()
        field_names = {r.field_name for r in rows}
        assert field_names == {'payment_status', 'amount_paid'}

        # old_value/new_value are Text columns -- SQLite coerces the numeric
        # values to their string form on storage (see status_change_log.py
        # module docstring: "stored as-is ... whatever str()-able value").
        amount_row = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO', field_name='amount_paid').one()
        assert amount_row.old_value == str(0.0)
        assert amount_row.new_value == str(250.50)

    def test_update_payment_status_same_partial_amount_logs_no_amount_paid_row(self, client, session):
        so = self._mk_so(session)
        so.payment_status = "Cash Sale - Partial"
        so.amount_paid = 250.50
        session.commit()
        before_count = StatusChangeLog.query.count()

        client.post(f"/sales-orders/{so.id}/payment-status",
                   data={"payment_status": "Cash Sale - Partial", "amount_paid": "250.50"})

        assert StatusChangeLog.query.count() == before_count


class TestStockOrderJobNumbers:
    _c = 0

    def _mk_so(self, session):
        TestStockOrderJobNumbers._c += 1
        n = TestStockOrderJobNumbers._c
        so = SalesOrder(so_number=f"REPORT-STO-{n:03d}", customer_name="Report Test Co",
                        status="Open", created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        return so, n

    def test_job_numbers_rolls_up_distinct_line_values(self, session):
        so, n = self._mk_so(session)
        sto = StockOrder(stock_order_number=f"REPORT-STO-NUM-{n:03d}", so_id=so.id, status="Open",
                         created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.flush()
        session.add_all([
            StockOrderLine(stock_order_id=sto.id, item_code="A1", description="A", qty=1.0, job_number="FM0100"),
            StockOrderLine(stock_order_id=sto.id, item_code="A2", description="B", qty=1.0, job_number="FM0100"),
            StockOrderLine(stock_order_id=sto.id, item_code="A3", description="C", qty=1.0, job_number="FM0101"),
            StockOrderLine(stock_order_id=sto.id, item_code="A4", description="D", qty=1.0, job_number=None),
        ])
        session.commit()

        assert sto.job_numbers == "FM0100, FM0101"

    def test_job_numbers_blank_when_none_set(self, session):
        so, n = self._mk_so(session)
        sto = StockOrder(stock_order_number=f"REPORT-STO-BLANK-{n:03d}", so_id=so.id, status="Open",
                         created_at=datetime.now(timezone.utc))
        session.add(sto)
        session.flush()
        session.add(StockOrderLine(stock_order_id=sto.id, item_code="A1", description="A", qty=1.0))
        session.commit()

        assert sto.job_numbers == ""


class TestBalanceDue:
    _c = 0

    def _mk_so(self, session, amount_paid=0.0):
        TestBalanceDue._c += 1
        n = TestBalanceDue._c
        so = SalesOrder(so_number=f"REPORT-BAL-{n:03d}", customer_name="Report Test Co",
                        status="Draft", payment_status="Cash Sale - Partial",
                        amount_paid=amount_paid, created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        return so

    def test_balance_due_computes_total_minus_amount_paid(self, session):
        so = self._mk_so(session, amount_paid=300.0)
        session.add(SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=1000.0))
        session.commit()

        assert so.balance_due == 700.0

    def test_balance_due_equals_total_incl_when_amount_paid_is_default(self, session):
        so = self._mk_so(session)  # amount_paid left at the 0.0 default
        session.add(SOLineItem(so_id=so.id, description="Line 1", qty=1.0, incl_total=500.0))
        session.commit()

        assert so.amount_paid == 0.0
        assert so.balance_due == so.total_incl == 500.0


class TestReportStatus:
    """SalesOrder.report_status / display_report_status -- computed property
    coverage across all real states, per Sequencing item 17 and Decision 1 of
    docs/specs/sales-order-report-excel-export-2026-07-17.md (the *all*-based
    Ready-Dispatch rule, not the earlier *any*-based draft)."""
    _c = 0

    def _mk_so(self, session, status='Draft'):
        TestReportStatus._c += 1
        n = TestReportStatus._c
        so = SalesOrder(so_number=f"REPORT-STATUS-{n:03d}", customer_name="Report Test Co",
                        status=status, created_at=datetime.now(timezone.utc))
        session.add(so)
        session.flush()
        return so, n

    def _mk_wo(self, session, so, n, status, suffix=""):
        wo = WorksOrder(wo_number=f"RS-WO-{n:03d}{suffix}", so_id=so.id,
                        order_type='ASSEMBLY', status=status)
        session.add(wo)
        return wo

    def _mk_sto(self, session, so, n, status, suffix=""):
        sto = StockOrder(stock_order_number=f"RS-STO-{n:03d}{suffix}", so_id=so.id, status=status)
        session.add(sto)
        return sto

    def test_loaded_when_no_wo_or_sto(self, session):
        so, n = self._mk_so(session)
        session.commit()
        assert so.report_status == 'Loaded'

    def test_released_when_wo_exists_and_not_terminal(self, session):
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Open')
        session.commit()
        assert so.report_status == 'Released'

    def test_released_when_sto_exists_and_not_terminal(self, session):
        so, n = self._mk_so(session, status='Open')
        self._mk_sto(session, so, n, 'Open')
        session.commit()
        assert so.report_status == 'Released'

    def test_ready_dispatch_when_single_wo_complete(self, session):
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Complete')
        session.commit()
        assert so.report_status == 'Ready-Dispatch'

    def test_ready_dispatch_when_all_terminal_mix_of_complete_and_cancelled(self, session):
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Complete', suffix='A')
        self._mk_wo(session, so, n, 'Cancelled', suffix='B')
        session.commit()
        assert so.report_status == 'Ready-Dispatch'

    def test_all_cancelled_stays_released_not_ready_dispatch(self, session):
        """Edge case called out explicitly in Decision 1: an SO whose WOs/STOs
        are all Cancelled (no completions at all) must NOT read as
        Ready-Dispatch -- the any_complete guard exists to avoid the vacuous-
        truth bug (all-terminal trivially satisfied by an all-Cancelled set)."""
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Cancelled', suffix='A')
        self._mk_sto(session, so, n, 'Cancelled', suffix='B')
        session.commit()
        assert so.report_status == 'Released'

    def test_multi_wo_partial_complete_stays_released(self, session):
        """Some-but-not-all Complete must read as Released, not
        Ready-Dispatch -- all_terminal requires every linked order terminal."""
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Complete', suffix='A')
        self._mk_wo(session, so, n, 'Open', suffix='B')
        session.commit()
        assert so.report_status == 'Released'

    def test_none_when_so_status_closed(self, session):
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Complete')
        session.commit()
        so.status = 'Closed'
        session.commit()
        assert so.report_status is None

    def test_none_when_so_status_cancelled(self, session):
        so, n = self._mk_so(session, status='Cancelled')
        session.commit()
        assert so.report_status is None

    def test_display_report_status_suffix_present_and_absent(self, session):
        so, n = self._mk_so(session, status='Open')
        self._mk_wo(session, so, n, 'Open')
        session.commit()
        assert so.report_status == 'Released'

        so.on_hold = False
        session.commit()
        assert so.display_report_status == 'Released'

        so.on_hold = True
        session.commit()
        assert so.display_report_status == 'Released — On Hold'


class TestUpdateReportNotes:
    """POST /sales-orders/<id>/report-notes -- see Sequencing item 8 of
    docs/specs/sales-order-report-excel-export-2026-07-17.md."""
    _c = 0

    def _mk_so(self, session, report_notes=None):
        TestUpdateReportNotes._c += 1
        n = TestUpdateReportNotes._c
        so = SalesOrder(so_number=f"REPORT-NOTES-{n:03d}", customer_name="Report Test Co",
                        status="Draft", report_notes=report_notes,
                        created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_update_report_notes_sets_value(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/report-notes", data={"report_notes": "Awaiting stock"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.report_notes == "Awaiting stock"

    def test_update_report_notes_logs_change_only_when_value_differs(self, client, session):
        so = self._mk_so(session, report_notes="Original note")
        before_count = StatusChangeLog.query.count()

        # Same value submitted -- no log row, no-op
        client.post(f"/sales-orders/{so.id}/report-notes", data={"report_notes": "Original note"})
        assert StatusChangeLog.query.count() == before_count

        # Different value -- exactly one log row
        client.post(f"/sales-orders/{so.id}/report-notes", data={"report_notes": "Updated note"})
        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO', field_name='report_notes').all()
        assert len(rows) == 1
        assert rows[0].old_value == "Original note"
        assert rows[0].new_value == "Updated note"

    def test_update_report_notes_blank_clears_value(self, client, session):
        so = self._mk_so(session, report_notes="Something")
        resp = client.post(f"/sales-orders/{so.id}/report-notes", data={"report_notes": "  "})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.report_notes is None


class TestSaveOrderCarryForward:
    """POST /sales-orders/save overwrite path must carry forward
    report_notes/on_hold/on_hold_reason/amount_paid onto the replacement
    SalesOrder row -- see Sequencing item 9 of docs/specs/
    sales-order-report-excel-export-2026-07-17.md Decision 3. The overwrite
    path only ever fires when no WO/STO is linked (guarded in save_order()),
    so no such fixtures are needed here."""
    _c = 0

    def _mk_so(self, session):
        TestSaveOrderCarryForward._c += 1
        n = TestSaveOrderCarryForward._c
        so = SalesOrder(so_number=f"CARRY-SO-{n:03d}", customer_name="Carry Forward Test Co",
                        status="Draft", report_notes="Manual note kept between uploads",
                        on_hold=True, on_hold_reason="Awaiting customer confirmation",
                        payment_status="Cash Sale - Partial", amount_paid=350.75,
                        created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_overwrite_preserves_all_four_carry_forward_fields(self, client, session):
        so = self._mk_so(session)
        so_number = so.so_number

        resp = client.post('/sales-orders/save', data={
            'so_number': so_number,
            'customer_name': 'Re-uploaded Customer Name',
            'line_items_json': '[]',
        })
        assert resp.status_code == 302

        reloaded = SalesOrder.query.filter_by(so_number=so_number).first()
        assert reloaded is not None
        assert reloaded.customer_name == 'Re-uploaded Customer Name'
        assert reloaded.report_notes == "Manual note kept between uploads"
        assert reloaded.on_hold is True
        assert reloaded.on_hold_reason == "Awaiting customer confirmation"
        assert reloaded.amount_paid == 350.75


class TestUpdateOnHold:
    """POST /sales-orders/<id>/on-hold -- see Sequencing item 10 of
    docs/specs/sales-order-report-excel-export-2026-07-17.md."""
    _c = 0

    def _mk_so(self, session, on_hold=False, on_hold_reason=None):
        TestUpdateOnHold._c += 1
        n = TestUpdateOnHold._c
        so = SalesOrder(so_number=f"ONHOLD-SO-{n:03d}", customer_name="On Hold Test Co",
                        status="Draft", on_hold=on_hold, on_hold_reason=on_hold_reason,
                        created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_toggle_on_sets_flag_and_reason(self, client, session):
        so = self._mk_so(session)
        resp = client.post(f"/sales-orders/{so.id}/on-hold",
                           data={"on_hold": "on", "on_hold_reason": "Waiting on payment"})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.on_hold is True
        assert updated.on_hold_reason == "Waiting on payment"

    def test_toggle_off_clears_flag(self, client, session):
        so = self._mk_so(session, on_hold=True, on_hold_reason="Some reason")
        resp = client.post(f"/sales-orders/{so.id}/on-hold", data={})
        assert resp.status_code == 302

        updated = db.session.get(SalesOrder, so.id)
        assert updated.on_hold is False

    def test_logs_on_hold_and_reason_as_separate_rows_when_both_change(self, client, session):
        so = self._mk_so(session)
        client.post(f"/sales-orders/{so.id}/on-hold",
                   data={"on_hold": "on", "on_hold_reason": "Awaiting stock"})

        rows = StatusChangeLog.query.filter_by(order_id=so.id, order_type='SO').all()
        field_names = {r.field_name for r in rows}
        assert field_names == {'on_hold', 'on_hold_reason'}

    def test_no_change_writes_no_log_rows(self, client, session):
        so = self._mk_so(session, on_hold=True, on_hold_reason="Steady state")
        before_count = StatusChangeLog.query.count()

        client.post(f"/sales-orders/{so.id}/on-hold",
                   data={"on_hold": "on", "on_hold_reason": "Steady state"})

        assert StatusChangeLog.query.count() == before_count

    def test_display_report_status_reflects_on_hold_overlay(self, session):
        so = self._mk_so(session, on_hold=True)
        assert so.display_report_status == "Loaded — On Hold"


class TestPaymentStatusDataMigration:
    """Exercises scripts/migrate_payment_status_values.py against the
    shared in-memory fixture DB -- never instance/sops.db."""
    _c = 0

    def _mk_so(self, session, payment_status):
        TestPaymentStatusDataMigration._c += 1
        n = TestPaymentStatusDataMigration._c
        so = SalesOrder(so_number=f"REPORT-MIG-{n:03d}", customer_name="Report Test Co",
                        status="Draft", payment_status=payment_status,
                        created_at=datetime.now(timezone.utc))
        session.add(so)
        session.commit()
        return so

    def test_direct_match_rows_map_exactly_as_specified(self, session):
        so_uptodate = self._mk_so(session, "Account - Up to Date")
        so_onhold = self._mk_so(session, "On Hold")
        so_partial = self._mk_so(session, "Partially Paid")

        migrate_payment_status_values(session)

        assert db.session.get(SalesOrder, so_uptodate.id).payment_status == "Account - Up to Date"
        assert db.session.get(SalesOrder, so_onhold.id).payment_status == "Account - On Hold"
        assert db.session.get(SalesOrder, so_partial.id).payment_status == "Cash Sale - Partial"

    def test_ambiguous_rows_map_to_documented_guess_and_are_flagged(self, session):
        so_pending = self._mk_so(session, "Pending")
        so_paid = self._mk_so(session, "Paid")
        so_unpaid = self._mk_so(session, "Unpaid")

        result = migrate_payment_status_values(session)

        assert db.session.get(SalesOrder, so_pending.id).payment_status == "Account - Pending"
        assert db.session.get(SalesOrder, so_paid.id).payment_status == "Cash Sale - Paid"
        assert db.session.get(SalesOrder, so_unpaid.id).payment_status == "Cash Sale - Unpaid"

        guessed_numbers = {so_number for so_number, _, _ in result['guessed']}
        assert so_pending.so_number in guessed_numbers
        assert so_paid.so_number in guessed_numbers
        assert so_unpaid.so_number in guessed_numbers

    def test_row_already_on_new_value_is_untouched_on_second_run(self, session):
        so = self._mk_so(session, "Pending")  # old-style value

        migrate_payment_status_values(session)
        assert db.session.get(SalesOrder, so.id).payment_status == "Account - Pending"

        # Second run: the row is now already on a new-list value, so it must
        # be skipped/left untouched, not re-flagged as a fresh guess.
        result2 = migrate_payment_status_values(session)
        assert db.session.get(SalesOrder, so.id).payment_status == "Account - Pending"
        assert so.so_number not in {so_number for so_number, _, _ in result2['guessed']}
