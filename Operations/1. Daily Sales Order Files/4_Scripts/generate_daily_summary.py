
import pandas as pd
import openpyxl
import re
import datetime
import os
import glob

# Configuration
def resolve_sales_report_file(dt):
    reports_dir = "3_Live_Reports"
    month_tag = dt.strftime("%m.%Y")
    preferred = os.path.join(reports_dir, f"Ops Sales Order Report - {month_tag}.xlsx")
    legacy = os.path.join(reports_dir, f"Sales Order Report - {month_tag}.xlsx")

    if os.path.exists(preferred):
        return preferred

    if os.path.exists(legacy):
        try:
            os.rename(legacy, preferred)
            return preferred
        except Exception:
            return legacy

    # Always use the current month output file when starting a new month.
    return preferred

excel_file = resolve_sales_report_file(datetime.datetime.now())

def get_latest_date_sheet(wb):
    date_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
    sheets = [s for s in wb.sheetnames if date_pattern.match(s)]
    
    if not sheets:
        return None
    
    try:
        sheets.sort(key=lambda s: datetime.datetime.strptime(s, "%d.%m.%Y"))
        return sheets[-1]
    except ValueError:
        return sheets[-1]

def generate_summary():
    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        latest_sheet = get_latest_date_sheet(wb)
        
        if not latest_sheet:
            print("No dated sheets found for summary.")
            return

        print(f"Generating summary for: {latest_sheet}")
        
        # Read the sheet with header at row 2 (index 1)
        df = pd.read_excel(excel_file, sheet_name=latest_sheet, header=1)
        
        # Filter out rows that are purely empty or total rows
        # Drop rows where 'Job Number' and 'SO Number' are both NaN
        # Use column names if available
        # Columns based on inspection:
        # ['Date', 'Delivery Date', 'Job Number', 'SO Number', 'Customer Ref.', 'Customer', 'Price Incl.', 'Sales Rep.', 'Status', 'Payment Type & Status', 'Details', 'Planned Collection / Delivery']
        
        # Clean up column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Filter valid orders
        # A valid order usually has a Job Number or SO Number
        valid_orders = df.dropna(subset=['Job Number', 'SO Number'], how='all')
        
        # Remove "Total" row if present in Job Number or SO Number
        valid_orders = valid_orders[~valid_orders['Job Number'].astype(str).str.contains('Total', case=False, na=False)]
        
        total_orders = len(valid_orders)
        
        # Calculate Total Value
        price_col = 'Total' if 'Total' in valid_orders.columns else 'Price Incl.'
        if price_col in valid_orders.columns:
            def clean_currency(val):
                if pd.isna(val): return 0.0
                if isinstance(val, (int, float)): return float(val)
                s = str(val)
                s = re.sub(r'[R,\s]', '', s)
                try:
                    return float(s)
                except ValueError:
                    return 0.0
            
            valid_orders[price_col] = valid_orders[price_col].apply(clean_currency)
            total_value = valid_orders[price_col].sum()
        else:
            total_value = 0.0

        # Analysis by Payment Status
        payment_col = 'Payment Status' if 'Payment Status' in valid_orders.columns else 'Payment Type & Status'
        if payment_col in valid_orders.columns:
            unpaid_cash = valid_orders[valid_orders[payment_col].str.contains('CASH SALE - UNPAID', case=False, na=False)]
            unpaid_count = len(unpaid_cash)
        else:
            unpaid_count = 0
            unpaid_cash = pd.DataFrame()

        # Analysis by Status
        status_col = 'Status'
        if status_col in valid_orders.columns:
            ready_dispatch = valid_orders[valid_orders[status_col].str.contains('Ready - Dispatch', case=False, na=False)]
            ready_count = len(ready_dispatch)
            ready_value = ready_dispatch[price_col].sum() if price_col in valid_orders.columns else 0.0
        else:
            ready_count = 0
            ready_value = 0.0

        # Print Executive Summary
        print("\n" + "="*40)
        print(f"EXECUTIVE SUMMARY: {latest_sheet}")
        print("="*40)
        print(f"Total Active Orders: {total_orders}")
        print(f"Total Value (Incl. VAT): R {total_value:,.2f}")
        print(f"Total Ready-Dispatch Value: R {ready_value:,.2f} ({ready_count} orders)")
        print("-" * 40)
        print(f"Action Items (Unpaid Cash Sales): {unpaid_count}")
        if unpaid_count > 0:
            for index, row in unpaid_cash.iterrows():
                job = row.get('Job Number', 'N/A')
                so = row.get('SO Number', 'N/A')
                customer = row.get('Customer', 'Unknown')
                amount = row.get(price_col, 0)
                print(f"  - {job}/{so}: {customer} (R {amount:,.2f})")
        
        print("-" * 40)
        print("="*40 + "\n")

    except Exception as e:
        print(f"Error generating summary: {e}")

def main():
    generate_summary()

if __name__ == "__main__":
    main()
