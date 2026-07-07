"""Shared Sage-PDF table parsing helpers.

Both the Sales Order parser (services/pdf_parser.py) and the Purchase Order
parser (services/po_parser.py) consume PDFs exported from the same Sage
template family - identical column geometry for the line-item table, only
the header fields differ. This module holds the geometry-dependent parsing
logic so a future template fix (see Batch 8's multi-page footer bug) only
needs to happen once. See docs/specs/purchase-order-module-plan.md section 3.
"""
from collections import defaultdict


def clean_numerical_str(val: str) -> float:
    """Strip currency/percent formatting and parse a float, defaulting to 0.0."""
    if not val:
        return 0.0
    val_str = str(val).replace('R', '').replace('%', '').replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0


def build_merged_lines(page):
    """Return coordinate-merged word lines for a single pdfplumber page."""
    words = page.extract_words()
    grouped = defaultdict(list)
    for w in words:
        grouped[round(w['top'])].append(w)
    sorted_ys = sorted(grouped.keys())
    merged = []
    current = []
    last_y = -100
    for y in sorted_ys:
        if y - last_y <= 3:
            current.extend(grouped[y])
        else:
            if current:
                merged.append(current)
            current = list(grouped[y])
            last_y = y
    if current:
        merged.append(current)
    return merged


def parse_line_item_row(line):
    """Split a word line into column buckets and return a line-item dict.

    Column x-thresholds match the shared Sage template used for both Sales
    Order and Purchase Order exports: Description / Quantity / Excl. Price /
    Disc % / VAT % / Excl. Total / Incl. Total.
    """
    desc_words, qty_words, price_words, disc_words, vat_words, excl_words, incl_words = [], [], [], [], [], [], []
    for w in line:
        x = w['x0']
        if x < 200:
            desc_words.append(w)
        elif x < 240:
            qty_words.append(w)
        elif x < 300:
            price_words.append(w)
        elif x < 350:
            disc_words.append(w)
        elif x < 410:
            vat_words.append(w)
        elif x < 500:
            excl_words.append(w)
        else:
            incl_words.append(w)

    def fw(wl):
        return " ".join([w['text'] for w in sorted(wl, key=lambda w: w['x0'])]).strip()

    desc = fw(desc_words)
    qty = fw(qty_words)
    price = fw(price_words)
    disc = fw(disc_words)
    vat = fw(vat_words)
    excl = fw(excl_words)
    incl = fw(incl_words)

    if not (qty or price or disc or vat or excl or incl):
        # Description-continuation row
        return {'continuation': True, 'desc': desc}

    qty_val = clean_numerical_str(qty)
    excl_val = clean_numerical_str(price)
    disc_val = clean_numerical_str(disc)
    vat_val = clean_numerical_str(vat)
    excl_tot = clean_numerical_str(excl)
    incl_tot = clean_numerical_str(incl)

    if excl_tot == 0.0 and qty_val > 0 and excl_val > 0:
        excl_tot = qty_val * excl_val
    if incl_tot == 0.0 and excl_tot > 0:
        incl_tot = excl_tot * (1 + (vat_val / 100.0))

    return {
        'continuation': False,
        'description': desc,
        'qty': qty_val,
        'excl_price': excl_val,
        'disc_pct': disc_val,
        'vat_pct': vat_val,
        'excl_total': excl_tot,
        'incl_total': incl_tot,
    }


def parse_line_items_all_pages(pdf, merged_lines_p1, footer_markers=("BANKING DETAILS", "Total Discount:")):
    """Walk every page of the PDF and return the flat list of parsed line items.

    Re-detects the 'Description/Quantity' table header on every page (it
    repeats per page in this template family) and stops scanning a page's
    rows once a footer marker is hit - but keeps processing subsequent
    pages, since the footer block repeats on every page too (see Batch 8's
    multi-page Sales Order regression).
    """
    line_items = []
    for page_idx, page in enumerate(pdf.pages):
        merged = build_merged_lines(page) if page_idx > 0 else merged_lines_p1
        table_started = False

        for line in merged:
            line_str = " ".join([w['text'] for w in sorted(line, key=lambda w: w['x0'])])

            if not table_started:
                if "Description" in line_str and "Quantity" in line_str:
                    table_started = True
                continue

            if any(marker in line_str for marker in footer_markers):
                break

            parsed_row = parse_line_item_row(line)
            if parsed_row['continuation']:
                if line_items and parsed_row['desc']:
                    line_items[-1]['description'] = (
                        line_items[-1]['description'] + " " + parsed_row['desc']
                    ).strip()
            else:
                line_items.append({
                    'description': parsed_row['description'],
                    'qty': parsed_row['qty'],
                    'excl_price': parsed_row['excl_price'],
                    'disc_pct': parsed_row['disc_pct'],
                    'vat_pct': parsed_row['vat_pct'],
                    'excl_total': parsed_row['excl_total'],
                    'incl_total': parsed_row['incl_total'],
                })
    return line_items
