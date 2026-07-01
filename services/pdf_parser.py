import pdfplumber
import re
import os
from collections import defaultdict
from datetime import datetime

def clean_numerical_str(val):
    if not val:
        return 0.0
    val_str = str(val).replace('R', '').replace('%', '').replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

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

            # ── Page 1: header fields + start of line items ───────────────────
            page1 = pdf.pages[0]
            raw_text_p1 = page1.extract_text() or ""
            result['raw_pdf_text'] = raw_text_p1

            # Collect raw text from ALL pages for the stored field
            all_raw_text = raw_text_p1
            for p in pdf.pages[1:]:
                all_raw_text += "\n" + (p.extract_text() or "")
            result['raw_pdf_text'] = all_raw_text

            def build_merged_lines(page):
                """Return coordinate-merged word lines for a single page."""
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

            # 3. Parse Line Items — all pages
            # Page 1: wait for "Description / Quantity" table header to start
            # Pages 2+: table already in progress, start immediately

            def parse_line_item_row(line):
                """Split a word line into column buckets and return a line-item dict or None."""
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

                desc  = fw(desc_words)
                qty   = fw(qty_words)
                price = fw(price_words)
                disc  = fw(disc_words)
                vat   = fw(vat_words)
                excl  = fw(excl_words)
                incl  = fw(incl_words)

                if not (qty or price or disc or vat or excl or incl):
                    # Description-continuation row
                    return {'continuation': True, 'desc': desc}

                qty_val  = clean_numerical_str(qty)
                excl_val = clean_numerical_str(price)
                disc_val = clean_numerical_str(disc)
                vat_val  = clean_numerical_str(vat)
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
                    'incl_total': incl_tot
                }

            table_started = False
            table_ended = False

            for page_idx, page in enumerate(pdf.pages):
                if table_ended:
                    break
                merged = build_merged_lines(page) if page_idx > 0 else merged_lines_p1
                # Pages 2+ — table is already in progress
                if page_idx > 0:
                    table_started = True

                for line in merged:
                    line_str = " ".join([w['text'] for w in sorted(line, key=lambda w: w['x0'])])

                    if not table_started:
                        if "Description" in line_str and "Quantity" in line_str:
                            table_started = True
                        continue

                    if "BANKING DETAILS" in line_str or "Total Discount:" in line_str:
                        table_ended = True
                        break

                    parsed_row = parse_line_item_row(line)
                    if parsed_row['continuation']:
                        if result['line_items'] and parsed_row['desc']:
                            result['line_items'][-1]['description'] = (
                                result['line_items'][-1]['description'] + " " + parsed_row['desc']
                            ).strip()
                    else:
                        result['line_items'].append({
                            'description': parsed_row['description'],
                            'qty': parsed_row['qty'],
                            'excl_price': parsed_row['excl_price'],
                            'disc_pct': parsed_row['disc_pct'],
                            'vat_pct': parsed_row['vat_pct'],
                            'excl_total': parsed_row['excl_total'],
                            'incl_total': parsed_row['incl_total'],
                        })

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
