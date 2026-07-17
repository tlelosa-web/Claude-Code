import csv
import math
import os
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime

from models import db, Item


def _safe_copy_for_reading(src):
    """Shadow-copy a file before reading it, so we never read a potentially
    locked live file. Copied in from AvgMovement's
    item_movement_report.py::safe_copy_for_reading() rather than importing
    across projects - see docs/specs/amu-minmax-reorder-suggestion-2026-07-17.md."""
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


def round_amu_half(val):
    """Round AMU up to the next 0.5 increment, 1 decimal place, minimum 1.0.
    Copied in verbatim from AvgMovement's item_movement_report.py::
    round_amu_half() - see docs/specs/amu-minmax-reorder-suggestion-2026-07-17.md."""
    if val <= 0:
        return 1.0
    rounded = math.ceil(val * 2) / 2
    return max(round(rounded, 1), 1.0)


def import_amu_minmax_from_csv(csv_path):
    """Parse ItemMovementReport.csv, update Item.amu / Item.suggested_min /
    Item.suggested_max for matching item codes present in the CSV. Returns
    (updated_count, unmatched_count). Never creates items, never touches
    qty_on_hand, qty_on_order, reorder_point, or max_level. Items not
    present in the CSV are left untouched (not force-defaulted).

    Format (adapted from AvgMovement's
    item_movement_report.py::parse_csv()): title row + 3 metadata rows,
    then repeating blocks of an item-name row ("Code - Description" or
    just "Code"), transaction rows (Date, Reference, Description,
    Customer/Supplier, Qty), ending in a "Total for Item:" row.

    Per transaction row: is_purchase = (Description == "Supplier Invoice"),
    is_sale = (Description == "Tax Invoice"). total_purchased is the sum of
    abs(qty) where is_purchase, total_sold is the sum of abs(qty) where
    is_sale, both accumulated per item code. Each item's transaction date
    range (min/max date) drives period_months.

    Min/Max reuses the already-imported Item.lead_time_weeks (Batch 32) -
    this importer never re-parses OutstandingPOByItemReport.csv or
    recomputes lead time.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    tmp_path = _safe_copy_for_reading(csv_path)
    total_purchased = defaultdict(float)
    total_sold = defaultdict(float)
    date_ranges = {}
    seen_codes = set()

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
                    # Columns: Date, Reference, Description, Customer/Supplier, Qty
                    desc = row[2].strip()
                    try:
                        qty = float(row[4].strip())
                    except ValueError:
                        qty = 0.0

                    is_purchase = desc == 'Supplier Invoice'
                    is_sale = desc == 'Tax Invoice'

                    if not current_item_code:
                        continue

                    if is_purchase:
                        total_purchased[current_item_code] += abs(qty)
                    if is_sale:
                        total_sold[current_item_code] += abs(qty)

                    if current_item_code not in date_ranges:
                        date_ranges[current_item_code] = {'min_date': dt, 'max_date': dt}
                    else:
                        dr = date_ranges[current_item_code]
                        if dt < dr['min_date']:
                            dr['min_date'] = dt
                        if dt > dr['max_date']:
                            dr['max_date'] = dt
                else:
                    # Item name row - format is "Code - Description" or just "Code"
                    if ' - ' in first:
                        current_item_code = first.split(' - ', 1)[0].strip()
                    else:
                        current_item_code = first

                    if current_item_code:
                        seen_codes.add(current_item_code)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    updated_count = 0
    unmatched_count = 0

    for code in sorted(seen_codes):
        item = Item.query.filter_by(code=code).first()
        if not item:
            unmatched_count += 1
            continue

        purchased = total_purchased.get(code, 0.0)
        sold = total_sold.get(code, 0.0)

        dr = date_ranges.get(code)
        if dr:
            period_months = max(
                1,
                (dr['max_date'].year - dr['min_date'].year) * 12
                + (dr['max_date'].month - dr['min_date'].month),
            )
        else:
            period_months = 1

        amu_raw = max(purchased, sold) / period_months
        amu = round_amu_half(amu_raw)

        lead_time_months = round(item.lead_time_weeks / 4.33, 1) if item.lead_time_weeks > 0 else 0.0
        lead_time_months = max(lead_time_months, 0.5)

        min_qty = round(amu * lead_time_months)
        if min_qty <= 0:
            min_qty = 1

        max_qty = min_qty + round(amu * 2)
        if max_qty <= min_qty:
            max_qty = min_qty * 2

        item.amu = amu
        item.suggested_min = min_qty
        item.suggested_max = max_qty

        updated_count += 1

    db.session.commit()
    return updated_count, unmatched_count
