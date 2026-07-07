"""Parser for Sage-exported Supplier Purchase Order PDFs.

Same template family as services/pdf_parser.py (Sales Orders) - see
docs/specs/purchase-order-module-plan.md sections 1 and 3. Header fields
differ (NUMBER/REFERENCE/DATE/DUE DATE/SUPPLIER VAT NO vs the SO
equivalents); line-item table geometry is identical and shared via
services/pdf_common.py.
"""
import re
from datetime import datetime

import pdfplumber

from services.pdf_common import build_merged_lines, parse_line_items_all_pages


def parse_purchase_order_pdf(pdf_path: str) -> dict:
    """Parse a Supplier Purchase Order PDF. Never raises - returns partial
    results with parse_errors populated on failure (see README.md's
    fault-tolerant parsing constraint)."""
    result = {
        'po_number': '',
        'reference': '',
        'po_date': None,
        'due_date': None,
        'overall_discount_pct': 0.0,
        'supplier_name': '',
        'supplier_vat': '',
        'line_items': [],
        'raw_pdf_text': '',
        'parse_errors': [],
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                result['parse_errors'].append("PDF has no pages.")
                return result

            page1 = pdf.pages[0]
            raw_text_p1 = page1.extract_text() or ""

            all_raw_text = raw_text_p1
            for p in pdf.pages[1:]:
                all_raw_text += "\n" + (p.extract_text() or "")
            result['raw_pdf_text'] = all_raw_text

            merged_lines_p1 = build_merged_lines(page1)

            po_match = re.search(r'NUMBER:\s*(PO\d+)', raw_text_p1)
            if po_match:
                result['po_number'] = po_match.group(1)
            else:
                po_match_fb = re.search(r'PO\d+', raw_text_p1)
                if po_match_fb:
                    result['po_number'] = po_match_fb.group(0)

            ref_match = re.search(r'REFERENCE:\s*(\S+)', raw_text_p1)
            if ref_match:
                result['reference'] = ref_match.group(1)

            # "DATE:" and "DUE DATE:" are both present - the lookbehind keeps
            # the plain DATE: match from also matching inside "DUE DATE:".
            po_date_match = re.search(r'(?<!DUE )DATE:\s*(\d{2}/\d{2}/\d{4})', raw_text_p1)
            if po_date_match:
                try:
                    result['po_date'] = datetime.strptime(po_date_match.group(1), '%d/%m/%Y').date()
                except ValueError as ex:
                    result['parse_errors'].append(f"Failed parsing PO date: {ex}")

            due_date_match = re.search(r'DUE DATE:\s*(\d{2}/\d{2}/\d{4})', raw_text_p1)
            if due_date_match:
                try:
                    result['due_date'] = datetime.strptime(due_date_match.group(1), '%d/%m/%Y').date()
                except ValueError as ex:
                    result['parse_errors'].append(f"Failed parsing due date: {ex}")

            disc_match = re.search(r'OVERALL DISCOUNT %:\s*([\d.]+)%', raw_text_p1)
            if disc_match:
                result['overall_discount_pct'] = float(disc_match.group(1))

            vat_match = re.search(r'SUPPLIER VAT NO:\s*(\d+)', raw_text_p1)
            if vat_match:
                result['supplier_vat'] = vat_match.group(1)

            # Supplier name - "TO" column, mirrors the SO parser's
            # customer_name coordinate extraction but reads the right-hand
            # block instead of the left ("FROM" is always Fan Movement).
            supplier_name_lines = []
            for line in merged_lines_p1:
                line = sorted(line, key=lambda w: w['x0'])
                line_y = round(line[0]['top']) if line else 0
                if 190 <= line_y <= 208:
                    right_words = [w for w in line if w['x0'] >= 300]
                    right_str = " ".join(w['text'] for w in sorted(right_words, key=lambda w: w['x0'])).strip()
                    if right_str and right_str != "TO":
                        supplier_name_lines.append(right_str)
            if supplier_name_lines:
                result['supplier_name'] = " ".join(supplier_name_lines).strip()

            result['line_items'] = parse_line_items_all_pages(pdf, merged_lines_p1)

    except Exception as e:
        result['parse_errors'].append(f"Unexpected error while parsing PDF: {str(e)}")

    if not result['po_number']:
        result['parse_errors'].append("Purchase Order number not found.")
    if not result['supplier_name']:
        result['parse_errors'].append("Supplier name not found.")
    if not result['line_items']:
        result['parse_errors'].append("No line items found.")

    return result


def split_item_code(description: str) -> tuple[str, str]:
    """Split a PO line description formatted '<item_code> - <description>'.

    Only splits on the FIRST ' - ' - descriptions often contain further
    ' - ' segments (e.g. "...080Frame Deg00 - 15 DEG") that must stay part
    of the description. Returns (code, remainder); if there's no ' - ' at
    all, returns ('', description) so the raw text is preserved rather than
    guessing.
    """
    if not description or ' - ' not in description:
        return '', description or ''
    code, remainder = description.split(' - ', 1)
    return code.strip(), remainder.strip()
