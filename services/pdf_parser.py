import pdfplumber
import re
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
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                result['parse_errors'].append("PDF has no pages.")
                return result
            
            page = pdf.pages[0]
            words = page.extract_words()
            raw_text = page.extract_text() or ""
            result['raw_pdf_text'] = raw_text

            # Group words by rounded top coordinate
            grouped_lines = defaultdict(list)
            for w in words:
                grouped_lines[round(w['top'])].append(w)
            
            # Merge lines that are within 3 points of each other
            sorted_ys = sorted(grouped_lines.keys())
            merged_lines = []
            current_line = []
            last_y = -100
            for y in sorted_ys:
                if y - last_y <= 3:
                    current_line.extend(grouped_lines[y])
                else:
                    if current_line:
                        merged_lines.append(current_line)
                    current_line = list(grouped_lines[y])
                    last_y = y
            if current_line:
                merged_lines.append(current_line)

            # 1. Regex parsing from full raw text for simple fields
            so_match = re.search(r'NUMBER:\s*(SO\d+)', raw_text)
            if so_match:
                result['so_number'] = so_match.group(1)
            else:
                # Fallback to general pattern
                so_match_fb = re.search(r'SO\d+', raw_text)
                if so_match_fb:
                    result['so_number'] = so_match_fb.group(0)

            ref_match = re.search(r'REFERENCE:\s*(\S+)', raw_text)
            if ref_match:
                result['reference'] = ref_match.group(1)

            sales_rep_match = re.search(r'SALES REP:\s*([^\n]+)', raw_text)
            if sales_rep_match:
                result['sales_rep'] = sales_rep_match.group(1).strip()

            vat_match = re.search(r'CUSTOMER VAT NO:\s*(\d+)', raw_text)
            if vat_match:
                result['customer_vat'] = vat_match.group(1)

            # Dates
            date_matches = re.findall(r'(\d{2}/\d{2}/\d{4})', raw_text)
            if len(date_matches) >= 2:
                # The first date is usually SO Date, second is Delivery Date
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

            # 2. Coordinate-based column parsing for Addresses & Customer Name
            customer_name_lines = []
            delivery_address_lines = []
            
            for line in merged_lines:
                # Sort words in line by x0
                line = sorted(line, key=lambda w: w['x0'])
                
                # Check for address block region (typically top y between 180 and 290)
                # Y: 191 is Customer Name line
                # Y: 213 is VAT line
                # Y: 226-280 is Address lines
                line_y = round(line[0]['top']) if line else 0
                
                if 180 <= line_y <= 290:
                    col1 = []  # Sender Postal
                    col2 = []  # Sender Delivery
                    col3 = []  # Customer Postal
                    col4 = []  # Customer Delivery
                    
                    for w in line:
                        x = w['x0']
                        if x < 150:
                            col1.append(w)
                        elif x < 300:
                            col2.append(w)
                        elif x < 440:
                            col3.append(w)
                        else:
                            col4.append(w)

                    def fmt(w_list):
                        return " ".join([w['text'] for w in sorted(w_list, key=lambda w: w['x0'])]).strip()

                    c3_str = fmt(col3)
                    c4_str = fmt(col4)
                    
                    # Customer Name line (Y around 191 to 205)
                    # FROM | TO is followed by:
                    # FAN MOVEMENT (PTY) LTD | ARCTIC AIR (PTY) LTD
                    if 190 <= line_y <= 208:
                        # Right side has the customer name
                        # We combine Col 3 & 4 or check Col 3/4 words
                        right_words = [w for w in line if w['x0'] >= 300]
                        right_str = fmt(right_words)
                        if right_str and right_str != "TO":
                            customer_name_lines.append(right_str)
                            
                    # Delivery address lines (Y from 230 to 280, Col 4)
                    if 220 <= line_y <= 280:
                        if c4_str and c4_str != "DELIVERY ADDRESS:":
                            delivery_address_lines.append(c4_str)

            if customer_name_lines:
                result['customer_name'] = " ".join(customer_name_lines).strip()
            
            if delivery_address_lines:
                result['delivery_address'] = ", ".join(delivery_address_lines).strip()

            # 3. Parse Line Items
            table_started = False
            table_ended = False
            
            for line in merged_lines:
                line_str = " ".join([w['text'] for w in sorted(line, key=lambda w: w['x0'])])
                
                if "Description" in line_str and "Quantity" in line_str:
                    table_started = True
                    continue
                    
                if not table_started or table_ended:
                    continue
                    
                if "BANKING DETAILS" in line_str or "Total Discount:" in line_str:
                    table_ended = True
                    continue
                
                # Split words into table columns based on x0
                desc_words = []
                qty_words = []
                price_words = []
                disc_words = []
                vat_words = []
                excl_words = []
                incl_words = []
                
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
                
                def fmt_words(w_list):
                    return " ".join([w['text'] for w in sorted(w_list, key=lambda w: w['x0'])]).strip()
                
                desc = fmt_words(desc_words)
                qty = fmt_words(qty_words)
                price = fmt_words(price_words)
                disc = fmt_words(disc_words)
                vat = fmt_words(vat_words)
                excl = fmt_words(excl_words)
                incl = fmt_words(incl_words)
                
                if qty or price or disc or vat or excl or incl:
                    # New line item row
                    qty_val = clean_numerical_str(qty)
                    excl_val = clean_numerical_str(price)
                    disc_val = clean_numerical_str(disc)
                    vat_val = clean_numerical_str(vat)
                    excl_tot = clean_numerical_str(excl)
                    incl_tot = clean_numerical_str(incl)

                    # In case of parsing mismatch, verify simple math
                    if excl_tot == 0.0 and qty_val > 0 and excl_val > 0:
                        excl_tot = qty_val * excl_val
                    if incl_tot == 0.0 and excl_tot > 0:
                        incl_tot = excl_tot * (1 + (vat_val / 100.0))

                    current_item = {
                        'description': desc,
                        'qty': qty_val,
                        'excl_price': excl_val,
                        'disc_pct': disc_val,
                        'vat_pct': vat_val,
                        'excl_total': excl_tot,
                        'incl_total': incl_tot
                    }
                    result['line_items'].append(current_item)
                else:
                    # Description continuation
                    if result['line_items'] and desc:
                        result['line_items'][-1]['description'] = (result['line_items'][-1]['description'] + " " + desc).strip()

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
