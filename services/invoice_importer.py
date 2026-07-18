"""Importer for Sage's CustomerInvoicesReport.csv (Monthly INV tab source).
See docs/specs/sales-order-report-excel-export-2026-07-17.md Decision 4.

Full upsert by `invoice_number` -- every Invoice column is 100% Sage-sourced
(no manual field to protect, unlike item_importer/po_by_item_importer), so
create-or-update-every-field is correct here.

Real header row (verified against `1. Daily Sales Order Files/2_Source_Data/
CustomerInvoicesReport.csv`, sibling project, same Sage export):
    sep=,
    "Date","Document No.","Customer Ref.","Customer","Sales Rep","Due Date",
    "Ant. Pmt.","Exclusive","VAT","Total Selling","Total Outstanding"
"Ant. Pmt." has no corresponding Invoice column and is ignored.
"""
import csv
import os
import shutil
import tempfile
from datetime import datetime

from models import db, Invoice


def _safe_copy_for_reading(src):
    """Shadow-copy a file before reading it, so we never read a potentially
    locked live file. Copied in from AvgMovement's
    item_movement_report.py::safe_copy_for_reading() -- same convention as
    services/po_by_item_importer.py / services/movement_history_importer.py."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(src)[1])
    tmp.close()
    shutil.copy2(src, tmp.name)
    return tmp.name


def _parse_date(s):
    """Parse DD/MM/YYYY (or DD/MM/YY) date strings. Returns None on failure
    or blank input."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    for fmt in ('%d/%m/%Y', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _clean_number(val):
    if val is None:
        return 0.0
    val_str = str(val).replace('R', '').replace(',', '').strip()
    if not val_str:
        return 0.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0


def import_invoices_from_csv(csv_path):
    """Parse CustomerInvoicesReport.csv, upsert Invoice rows by
    invoice_number (full upsert -- every field is Sage-sourced). Rows with a
    missing `Document No.` or an unparseable `Date`/`Due Date` are skipped
    and counted, not raised as errors (fault-tolerant, matching the other
    importers' convention).

    Returns (created_count, updated_count, skipped_count).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    tmp_path = _safe_copy_for_reading(csv_path)
    created_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        with open(tmp_path, 'r', encoding='utf-8-sig', newline='') as f:
            first_line = f.readline()
            if not first_line.lower().startswith('sep='):
                f.seek(0)

            reader = csv.DictReader(f)

            for row in reader:
                invoice_number = (row.get('Document No.') or '').strip()
                if not invoice_number:
                    skipped_count += 1
                    continue

                invoice_date = _parse_date(row.get('Date'))
                due_date = _parse_date(row.get('Due Date'))
                if invoice_date is None or due_date is None:
                    skipped_count += 1
                    continue

                customer_ref = (row.get('Customer Ref.') or '').strip() or None
                customer_name = (row.get('Customer') or '').strip() or None
                sales_rep = (row.get('Sales Rep') or '').strip() or None
                exclusive = _clean_number(row.get('Exclusive'))
                vat = _clean_number(row.get('VAT'))
                total_selling = _clean_number(row.get('Total Selling'))
                total_outstanding = _clean_number(row.get('Total Outstanding'))

                invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()

                if invoice:
                    invoice.customer_ref = customer_ref
                    invoice.customer_name = customer_name
                    invoice.sales_rep = sales_rep
                    invoice.invoice_date = invoice_date
                    invoice.due_date = due_date
                    invoice.exclusive = exclusive
                    invoice.vat = vat
                    invoice.total_selling = total_selling
                    invoice.total_outstanding = total_outstanding
                    updated_count += 1
                else:
                    invoice = Invoice(
                        invoice_number=invoice_number,
                        customer_ref=customer_ref,
                        customer_name=customer_name,
                        sales_rep=sales_rep,
                        invoice_date=invoice_date,
                        due_date=due_date,
                        exclusive=exclusive,
                        vat=vat,
                        total_selling=total_selling,
                        total_outstanding=total_outstanding,
                    )
                    db.session.add(invoice)
                    created_count += 1

                if (created_count + updated_count) % 100 == 0:
                    db.session.commit()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    db.session.commit()
    return created_count, updated_count, skipped_count
