import csv
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime

from models import db, Item


def _safe_copy_for_reading(src):
    """Shadow-copy a file before reading it, so we never read a potentially
    locked live file. Copied in from AvgMovement's
    item_movement_report.py::safe_copy_for_reading() rather than importing
    across projects - see docs/specs/supplier-lead-time-import-2026-07-17.md."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(src)[1])
    tmp.close()
    shutil.copy2(src, tmp.name)
    return tmp.name


def _parse_date(s):
    """Parse DD/MM/YYYY (or DD/MM/YY) date strings. Returns None on failure."""
    s = s.strip()
    for fmt in ('%d/%m/%Y', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def import_supplier_lead_time_from_csv(csv_path):
    """Parse OutstandingPOByItemReport.csv, update Item.supplier /
    Item.lead_time_weeks for matching item codes. Returns (updated_count,
    unmatched_count). Never creates new items, never touches qty_on_hand,
    qty_on_order, or any other Item field.

    Format (adapted from AvgMovement's
    item_movement_report.py::parse_po_by_item()): title row + 3 metadata
    rows, then repeating blocks of an item-name row ("Code - Description"
    or just "Code"), transaction rows (Date, Reference, Order No.,
    Supplier, Delivery Date, Status, Qty, ...), ending in a
    "Total for Item:" row.

    Per item:
      - supplier: the most-frequent Supplier value across that item's PO
        rows (mode by transaction count).
      - lead_time_weeks: average of (Delivery Date - Date) in weeks,
        across rows with a valid, non-negative delivery date.

    On-order/pending PO quantity is deliberately not parsed or stored -
    SOPS already computes qty_on_order live from its own PurchaseOrders
    (see services/demand.py) and this importer must not recreate a second,
    conflicting source for it.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    tmp_path = _safe_copy_for_reading(csv_path)
    supplier_counts = defaultdict(Counter)
    lead_times = defaultdict(list)

    try:
        with open(tmp_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)

            # Skip title row
            try:
                next(reader)
            except StopIteration:
                return 0, 0

            # Skip metadata rows 1-3
            for _ in range(3):
                try:
                    next(reader)
                except StopIteration:
                    break

            current_item_code = ''

            for row in reader:
                if not row or not row[0].strip():
                    continue

                first = row[0].strip()

                # "Total for Item:" line -> end of current item block
                if first.lower().startswith('total for item:'):
                    current_item_code = ''
                    continue

                dt = _parse_date(first)
                if dt and len(row) >= 5:
                    # Columns: Date, Reference, Order No., Supplier, Delivery Date, Status, Qty, ...
                    supplier = row[3].strip()
                    delivery_date = _parse_date(row[4].strip())

                    # Extract item code from combined "Code - Description" name
                    if current_item_code and ' - ' in current_item_code:
                        code_part = current_item_code.split(' - ', 1)[0].strip()
                    else:
                        code_part = current_item_code

                    if not code_part:
                        continue

                    if supplier:
                        supplier_counts[code_part][supplier] += 1

                    if delivery_date:
                        days_diff = (delivery_date - dt).days
                        weeks = days_diff / 7.0
                        if weeks >= 0:  # Only valid, non-negative lead times
                            lead_times[code_part].append(weeks)
                else:
                    # Item name row
                    current_item_code = first
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    all_codes = set(supplier_counts.keys()) | set(lead_times.keys())

    updated_count = 0
    unmatched_count = 0

    for code in sorted(all_codes):
        item = Item.query.filter_by(code=code).first()
        if not item:
            unmatched_count += 1
            continue

        if supplier_counts.get(code):
            item.supplier = supplier_counts[code].most_common(1)[0][0]

        if lead_times.get(code):
            item.lead_time_weeks = round(sum(lead_times[code]) / len(lead_times[code]), 1)

        updated_count += 1

    db.session.commit()
    return updated_count, unmatched_count
