import re
import os
from datetime import datetime

import pdfplumber

from services.pdf_common import build_merged_lines, parse_line_items_all_pages


def clean_numerical_str(val):
    """Kept here for backward compatibility with any external importers.

    Canonical implementation now lives in services/pdf_common.py.
    """
    from services.pdf_common import clean_numerical_str as _clean
    return _clean(val)


def parse_sales_order_pdf(pdf_path):
    result = {
        'so_number': '',
        'job_numbers': '',
        'reference': '',
        'so_date': None,
        'delivery_date': None,
        'customer_name': '',
        'customer_vat': '',
        'delivery_address': '',
        'sales_rep': '',
        'line_items': [],
        'raw_pdf_text': '',
        'parse_errors': []
    }

    try:
        filename = os.path.basename(pdf_path)
        job_match = re.match(r'\s*((?:FM\d+\s*(?:-\s*FM\d+)?)(?:\s*,\s*FM\d+\s*(?:-\s*FM\d+)?)*)', filename, re.IGNORECASE)
        if job_match:
            result['job_numbers'] = re.sub(r'\s*-\s*', '-', job_match.group(1).strip().upper())

        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                result['parse_errors'].append("PDF has no pages.")
                return result

            # -- Page 1: header fields + start of line items --------------
            page1 = pdf.pages[0]
            raw_text_p1 = page1.extract_text() or ""
            result['raw_pdf_text'] = raw_text_p1

            # Collect raw text from ALL pages for the stored field
            all_raw_text = raw_text_p1
            for p in pdf.pages[1:]:
                all_raw_text += "\n" + (p.extract_text() or "")
            result['raw_pdf_text'] = all_raw_text

            merged_lines_p1 = build_merged_lines(page1)

            # 1. Regex parsing from page-1 raw text for simple fields
            so_match = re.search(r'NUMBER:\s*(SO\d+)', raw_text_p1)
            if so_match:
                result['so_number'] = so_match.group(1)
            else:
                so_match_fb = re.search(r'SO\d+', raw_text_p1)
                if so_match_fb:
                    result['so_number'] = so_match_fb.group(0)

            ref_match = re.search(r'REFERENCE:\s*(\S+)', raw_text_p1)
            if ref_match:
                result['reference'] = ref_match.group(1)

            sales_rep_match = re.search(r'SALES REP:\s*([^\n]+)', raw_text_p1)
            if sales_rep_match:
                result['sales_rep'] = sales_rep_match.group(1).strip()

            vat_match = re.search(r'CUSTOMER VAT NO:\s*(\d+)', raw_text_p1)
            if vat_match:
                result['customer_vat'] = vat_match.group(1)

            # Dates
            date_matches = re.findall(r'(\d{2}/\d{2}/\d{4})', raw_text_p1)
            if len(date_matches) >= 2:
                try:
                    result['so_date'] = datetime.strptime(date_matches[0], '%d/%m/%Y').date()
                    result['delivery_date'] = datetime.strptime(date_matches[1], '%d/%m/%Y').date()
                except Exception as ex:
                    result['parse_errors'].append(f"Failed parsing dates: {ex}")
            elif len(date_matches) == 1:
                try:
                    result['so_date'] = datetime.strptime(date_matches[0], '%d/%m/%Y').date()
                    result['delivery_date'] = result['so_date']
                except Exception as ex:
                    result['parse_errors'].append(f"Failed parsing single date: {ex}")

            # 2. Coordinate-based column parsing for Addresses & Customer Name (page 1 only)
            customer_name_lines = []
            delivery_address_lines = []

            for line in merged_lines_p1:
                line = sorted(line, key=lambda w: w['x0'])
                line_y = round(line[0]['top']) if line else 0

                if 180 <= line_y <= 290:
                    col3 = []
                    col4 = []
                    for w in line:
                        x = w['x0']
                        if x < 440:
                            if x >= 300:
                                col3.append(w)
                        else:
                            col4.append(w)

                    def fmt(w_list):
                        return " ".join([w['text'] for w in sorted(w_list, key=lambda w: w['x0'])]).strip()

                    c4_str = fmt(col4)

                    if 190 <= line_y <= 208:
                        right_words = [w for w in line if w['x0'] >= 300]
                        right_str = fmt(right_words)
                        if right_str and right_str != "TO":
                            customer_name_lines.append(right_str)

                    if 220 <= line_y <= 280:
                        if c4_str and c4_str != "DELIVERY ADDRESS:":
                            delivery_address_lines.append(c4_str)

            if customer_name_lines:
                result['customer_name'] = " ".join(customer_name_lines).strip()
            if delivery_address_lines:
                result['delivery_address'] = ", ".join(delivery_address_lines).strip()

            # 3. Parse Line Items -- all pages (shared geometry, see pdf_common)
            result['line_items'] = parse_line_items_all_pages(pdf, merged_lines_p1)

    except Exception as e:
        result['parse_errors'].append(f"Unexpected error while parsing PDF: {str(e)}")

    # Clean empty/error fields and validate
    if not result['so_number']:
        result['parse_errors'].append("Sales Order number not found.")
    if not result['customer_name']:
        result['parse_errors'].append("Customer name not found.")
    if not result['line_items']:
        result['parse_errors'].append("No line items found.")

    return result
