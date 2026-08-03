"""Tests for services/invoice_importer.py -- CustomerInvoicesReport.csv
importer. See docs/specs/sales-order-report-excel-export-2026-07-17.md
Decision 4.
"""
import os

from models import Invoice


def _write_invoice_csv(tmp_path, rows, filename='CustomerInvoicesReport.csv'):
    """Write a fixture CSV mirroring the real Sage export format: a leading
    `sep=,` line, then the real header row, then data rows. `rows` is a list
    of dicts using the exact Sage column names."""
    filepath = os.path.join(tmp_path, filename)
    header = ['Date', 'Document No.', 'Customer Ref.', 'Customer', 'Sales Rep',
              'Due Date', 'Ant. Pmt.', 'Exclusive', 'VAT', 'Total Selling',
              'Total Outstanding']
    with open(filepath, 'w', newline='') as f:
        f.write('sep=,\n')
        f.write(','.join(f'"{h}"' for h in header) + '\n')
        for row in rows:
            values = [str(row.get(h, '')) for h in header]
            f.write(','.join(f'"{v}"' for v in values) + '\n')
    return filepath


class TestImportInvoicesFromCsv:

    def test_creates_new_invoices(self, app, db, session, tmp_path):
        from services.invoice_importer import import_invoices_from_csv

        rows = [
            {'Date': '01/07/2026', 'Document No.': 'INV4717', 'Customer Ref.': 'SP734189',
             'Customer': 'D-Teq Air (Pty) Ltd', 'Sales Rep': 'GP - South',
             'Due Date': '30/08/2026', 'Ant. Pmt.': '', 'Exclusive': '1743',
             'VAT': '261.45', 'Total Selling': '2004.45', 'Total Outstanding': '2004.45'},
            {'Date': '01/07/2026', 'Document No.': 'INV4718', 'Customer Ref.': 'FM4185',
             'Customer': 'Cool Guys', 'Sales Rep': 'GP - East',
             'Due Date': '31/07/2026', 'Ant. Pmt.': '', 'Exclusive': '8949',
             'VAT': '1342.35', 'Total Selling': '10291.35', 'Total Outstanding': '0'},
        ]
        filepath = _write_invoice_csv(str(tmp_path), rows)

        created, updated, skipped = import_invoices_from_csv(filepath)

        assert created == 2
        assert updated == 0
        assert skipped == 0

        inv = Invoice.query.filter_by(invoice_number='INV4717').first()
        assert inv is not None
        assert inv.customer_ref == 'SP734189'
        assert inv.customer_name == 'D-Teq Air (Pty) Ltd'
        assert inv.sales_rep == 'GP - South'
        assert inv.invoice_date.isoformat() == '2026-07-01'
        assert inv.due_date.isoformat() == '2026-08-30'
        assert inv.exclusive == 1743.0
        assert inv.vat == 261.45
        assert inv.total_selling == 2004.45
        assert inv.total_outstanding == 2004.45

    def test_upserts_by_invoice_number_on_second_run(self, app, db, session, tmp_path):
        """Re-running the importer with a changed value for an existing
        invoice_number updates the row (full upsert), not a duplicate."""
        from services.invoice_importer import import_invoices_from_csv

        rows_1 = [
            {'Date': '01/07/2026', 'Document No.': 'INV5000', 'Customer Ref.': 'FM5000',
             'Customer': 'Original Customer', 'Sales Rep': 'GP - East',
             'Due Date': '31/07/2026', 'Ant. Pmt.': '', 'Exclusive': '1000',
             'VAT': '150', 'Total Selling': '1150', 'Total Outstanding': '1150'},
        ]
        filepath_1 = _write_invoice_csv(str(tmp_path), rows_1, filename='run1.csv')
        created, updated, skipped = import_invoices_from_csv(filepath_1)
        assert created == 1
        assert updated == 0

        rows_2 = [
            {'Date': '01/07/2026', 'Document No.': 'INV5000', 'Customer Ref.': 'FM5000',
             'Customer': 'Updated Customer', 'Sales Rep': 'GP - East',
             'Due Date': '31/07/2026', 'Ant. Pmt.': '', 'Exclusive': '1000',
             'VAT': '150', 'Total Selling': '1150', 'Total Outstanding': '0'},
        ]
        filepath_2 = _write_invoice_csv(str(tmp_path), rows_2, filename='run2.csv')
        created, updated, skipped = import_invoices_from_csv(filepath_2)

        assert created == 0
        assert updated == 1
        assert skipped == 0
        assert Invoice.query.filter_by(invoice_number='INV5000').count() == 1

        inv = Invoice.query.filter_by(invoice_number='INV5000').first()
        assert inv.customer_name == 'Updated Customer'
        assert inv.total_outstanding == 0.0

    def test_skips_missing_document_no_and_malformed_date(self, app, db, session, tmp_path):
        from services.invoice_importer import import_invoices_from_csv

        rows = [
            {'Date': '01/07/2026', 'Document No.': '', 'Customer Ref.': 'FM6000',
             'Customer': 'No Doc No', 'Sales Rep': 'GP - East',
             'Due Date': '31/07/2026', 'Ant. Pmt.': '', 'Exclusive': '1000',
             'VAT': '150', 'Total Selling': '1150', 'Total Outstanding': '1150'},
            {'Date': 'not-a-date', 'Document No.': 'INV6001', 'Customer Ref.': 'FM6001',
             'Customer': 'Bad Date', 'Sales Rep': 'GP - East',
             'Due Date': '31/07/2026', 'Ant. Pmt.': '', 'Exclusive': '1000',
             'VAT': '150', 'Total Selling': '1150', 'Total Outstanding': '1150'},
            {'Date': '01/07/2026', 'Document No.': 'INV6002', 'Customer Ref.': 'FM6002',
             'Customer': 'Good Row', 'Sales Rep': 'GP - East',
             'Due Date': '31/07/2026', 'Ant. Pmt.': '', 'Exclusive': '1000',
             'VAT': '150', 'Total Selling': '1150', 'Total Outstanding': '1150'},
        ]
        filepath = _write_invoice_csv(str(tmp_path), rows)

        created, updated, skipped = import_invoices_from_csv(filepath)

        assert created == 1
        assert updated == 0
        assert skipped == 2
        assert Invoice.query.filter_by(invoice_number='INV6002').first() is not None
        assert Invoice.query.filter_by(invoice_number='INV6001').first() is None
