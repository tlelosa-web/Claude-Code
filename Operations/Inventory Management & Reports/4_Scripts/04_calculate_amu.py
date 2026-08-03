"""
04_calculate_amu.py
-------------------
Dual-Source AMU Calculator + Supplier & Lead Time Extraction.

Source 1: CustomerSalesOrdersByCustomer.csv  (qty SOLD per month)
Source 2: OutstandingPOByItemReport.csv      (qty BOUGHT per month + Supplier + Lead Time)

Outputs:
  amu_lookup.pkl        — {Description: AMU} (sales-based, primary)
  amu_po_lookup.pkl     — {Code: AMU} (PO-based, fallback)
  po_supplier_lookup.pkl — {Code: Supplier}
  po_leadtime_lookup.pkl — {Code: avg_lead_time_in_months}
"""

import pandas as pd
import traceback
import os
import re
from datetime import datetime
from math import ceil

def log_error(msg):
    with open(r"1_Documentation\GEMINI.md", "a", encoding="utf-8") as f:
        f.write(f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {msg}\n")
    print(f"ERROR: {msg}")


# ═══════════════════════════════════════════════════════════════════
# SOURCE 1: Sales Orders (qty sold)
# ═══════════════════════════════════════════════════════════════════
def parse_sales_orders():
    """Parse CustomerSalesOrdersByCustomer.csv and return {Description: AMU}."""
    csv_path = r"2_Source_Data\CustomerSalesOrdersByCustomer.csv"
    if not os.path.exists(csv_path):
        print("  Notice: CustomerSalesOrdersByCustomer.csv not found. Skipping sales AMU.")
        return {}

    try:
        df = pd.read_csv(csv_path, skiprows=2, encoding='utf-8-sig',
                         on_bad_lines='skip', header=None,
                         names=['Name_Date', 'Reference', 'Status', 'Description', 'Qty', 'Total_Selling'])
    except Exception:
        df = pd.read_csv(csv_path, skiprows=2, encoding='latin1',
                         on_bad_lines='skip', header=None,
                         names=['Name_Date', 'Reference', 'Status', 'Description', 'Qty', 'Total_Selling'])

    records = []
    current_date = None

    for _, row in df.iterrows():
        name_date = str(row['Name_Date']).strip() if pd.notna(row['Name_Date']) else ''
        ref = str(row['Reference']).strip() if pd.notna(row['Reference']) else ''
        desc = str(row['Description']).strip() if pd.notna(row['Description']) else ''
        qty = row['Qty']

        if name_date.startswith('Total for'):
            continue

        if ref.startswith('SO') and name_date:
            for fmt in ('%d/%m/%Y', '%Y/%m/%d', '%m/%d/%Y', '%d-%m-%Y'):
                try:
                    current_date = datetime.strptime(name_date, fmt)
                    break
                except ValueError:
                    continue
            continue

        if desc and desc != 'nan' and pd.notna(qty):
            try:
                qty_val = float(qty)
            except (ValueError, TypeError):
                continue

            skip_keywords = ['delivery', 'transport', 'discount', 'freight',
                             'courier', 'shipping', 'collection']
            if any(kw in desc.lower() for kw in skip_keywords):
                continue

            if current_date is not None:
                records.append({
                    'Date': current_date,
                    'Description': desc,
                    'Qty': abs(qty_val)
                })

    if not records:
        print("  Warning: No item records parsed from sales orders.")
        return {}

    df_sales = pd.DataFrame(records)
    grouped = df_sales.groupby('Description').agg(
        Total_Qty=('Qty', 'sum'),
        Earliest_Date=('Date', 'min')
    ).reset_index()

    today = datetime.now()
    grouped['Months_Span'] = grouped['Earliest_Date'].apply(
        lambda d: max(1, ceil((today - d).days / 30.44))
    )
    grouped['AMU'] = (grouped['Total_Qty'] / grouped['Months_Span']).round(2)

    sales_amu = dict(zip(grouped['Description'], grouped['AMU']))
    print(f"  Sales AMU: {len(sales_amu)} unique items parsed.")
    return sales_amu


# ═══════════════════════════════════════════════════════════════════
# SOURCE 2: Purchase Orders (qty bought + supplier + lead time)
# ═══════════════════════════════════════════════════════════════════
def parse_purchase_orders():
    """
    Parse OutstandingPOByItemReport.csv and return:
      po_amu:      {Code: AMU}
      po_supplier: {Code: Supplier}
      po_leadtime: {Code: avg_lead_time_months}
    """
    csv_path = r"2_Source_Data\OutstandingPOByItemReport.csv"
    if not os.path.exists(csv_path):
        print("  Notice: OutstandingPOByItemReport.csv not found. Skipping PO data.")
        return {}, {}, {}

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except Exception:
        with open(csv_path, 'r', encoding='latin1') as f:
            lines = f.readlines()

    data_lines = lines[6:]  # Skip 6 header rows

    records = []
    current_item_code = None

    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(',')

        if parts[0].startswith('Total for Item:'):
            continue

        date_pattern = re.match(r'^\d{2}/\d{2}/\d{4}', parts[0])

        if not date_pattern:
            # Item header row
            full_name = line.rstrip(',')
            if ' - ' in full_name:
                current_item_code = full_name.split(' - ', 1)[0].strip()
            else:
                current_item_code = full_name.strip()
            continue

        # PO line: Date, Reference, Order No., Supplier, Delivery Date, Status, Qty, Unit Price, Total
        if current_item_code and len(parts) >= 9:
            try:
                po_date = datetime.strptime(parts[0].strip(), '%d/%m/%Y')
                supplier = parts[3].strip()
                delivery_str = parts[4].strip()
                qty_val = abs(float(parts[6].strip()))

                # Parse delivery date for lead time calculation
                try:
                    delivery_date = datetime.strptime(delivery_str, '%d/%m/%Y')
                    lead_days = (delivery_date - po_date).days
                    if lead_days < 0:
                        lead_days = 0
                except ValueError:
                    lead_days = None

                records.append({
                    'Date': po_date,
                    'Code': current_item_code,
                    'Supplier': supplier if supplier else None,
                    'Qty': qty_val,
                    'Lead_Days': lead_days
                })
            except (ValueError, TypeError, IndexError):
                continue

    if not records:
        print("  Warning: No item records parsed from purchase orders.")
        return {}, {}, {}

    df_po = pd.DataFrame(records)

    # --- AMU ---
    grouped_amu = df_po.groupby('Code').agg(
        Total_Qty=('Qty', 'sum'),
        Earliest_Date=('Date', 'min')
    ).reset_index()
    today = datetime.now()
    grouped_amu['Months_Span'] = grouped_amu['Earliest_Date'].apply(
        lambda d: max(1, ceil((today - d).days / 30.44))
    )
    grouped_amu['AMU'] = (grouped_amu['Total_Qty'] / grouped_amu['Months_Span']).round(2)
    po_amu = dict(zip(grouped_amu['Code'], grouped_amu['AMU']))

    # --- Supplier (most recent PO's supplier per item) ---
    df_po_sorted = df_po.dropna(subset=['Supplier']).sort_values('Date')
    supplier_last = df_po_sorted.drop_duplicates(subset='Code', keep='last')
    po_supplier = dict(zip(supplier_last['Code'], supplier_last['Supplier']))

    # --- Average Lead Time (in months) ---
    df_lt = df_po.dropna(subset=['Lead_Days'])
    if not df_lt.empty:
        avg_lt = df_lt.groupby('Code')['Lead_Days'].mean().reset_index()
        avg_lt['Lead_Time_Months'] = (avg_lt['Lead_Days'] / 30.44).round(2)
        po_leadtime = dict(zip(avg_lt['Code'], avg_lt['Lead_Time_Months']))
    else:
        po_leadtime = {}

    print(f"  PO AMU: {len(po_amu)} items | Suppliers: {len(po_supplier)} | Lead Times: {len(po_leadtime)}")
    return po_amu, po_supplier, po_leadtime


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def calculate_amu():
    try:
        print("Starting 04_calculate_amu.py (Dual-Source + Supplier + Lead Time)...")

        sales_amu = parse_sales_orders()
        po_amu, po_supplier, po_leadtime = parse_purchase_orders()

        # Save all lookups
        pd.to_pickle(sales_amu, r"5_Archive_and_Debug\amu_sales_lookup.pkl")
        pd.to_pickle(po_amu, r"5_Archive_and_Debug\amu_po_lookup.pkl")
        pd.to_pickle(po_supplier, r"5_Archive_and_Debug\po_supplier_lookup.pkl")
        pd.to_pickle(po_leadtime, r"5_Archive_and_Debug\po_leadtime_lookup.pkl")

        # Combined AMU (sales-primary)
        combined = dict(sales_amu)
        pd.to_pickle(combined, r"5_Archive_and_Debug\amu_lookup.pkl")

        # Debug log
        with open(r"5_Archive_and_Debug\debug_output_utf8.txt", "w", encoding="utf-8") as f:
            f.write("AMU + Supplier + Lead Time Calculation Successful.\n")
            f.write(f"Sales AMU items: {len(sales_amu)}\n")
            f.write(f"PO AMU items: {len(po_amu)}\n")
            f.write(f"PO Suppliers mapped: {len(po_supplier)}\n")
            f.write(f"PO Lead Times mapped: {len(po_leadtime)}\n")

        print(f"Successfully calculated: {len(sales_amu)} sales AMU, {len(po_amu)} PO AMU, "
              f"{len(po_supplier)} suppliers, {len(po_leadtime)} lead times.")

    except Exception as e:
        err_msg = f"04_calculate_amu failed: {str(e)}\n{traceback.format_exc()}"
        log_error(err_msg)
        exit(1)

if __name__ == "__main__":
    calculate_amu()
