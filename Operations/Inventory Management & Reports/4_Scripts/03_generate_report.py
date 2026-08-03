"""
03_generate_report.py
---------------------
Generates 3-tab Live Inventory Report styled to match ImportStockFinal.xlsx.

Style: Aptos Narrow font, title row, clean non-bold headers,
       center+top aligned, text-wrapped, ZAR accounting format.
"""
import pandas as pd
import traceback
from datetime import datetime
import os
import tempfile
import shutil

def log_error(msg):
    with open(r"1_Documentation\GEMINI.md", "a", encoding="utf-8") as f:
        f.write(f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {msg}\n")
    print(f"ERROR: {msg}")


def apply_sheet_formatting(workbook, worksheet, df, sheet_title, formats):
    """Apply consistent ImportStockFinal-style formatting to a worksheet."""
    title_fmt, header_fmt, text_fmt, num_fmt, acct_fmt, wrap_fmt = formats
    
    num_cols = len(df.columns)
    
    # --- Row 1: Title row (merged, bold, 12pt) ---
    worksheet.merge_range(0, 0, 0, num_cols - 1, sheet_title, title_fmt)
    worksheet.set_row(0, 18)  # Title row height ~18
    # --- Row 2: Headers (bold, center+top, text-wrapped) ---
    worksheet.set_row(1, 43)  # Row height 43 to match ImportStockFinal
    for col_num, col_name in enumerate(df.columns):
        worksheet.write(1, col_num, col_name, header_fmt)

    # --- Data rows starting at row 3 (index 2) ---
    cost_columns = ['Cost Price', 'Order Cost', 'Stock Value', 'Order Value']
    numeric_columns = [
        'Safety Stock', 'Lead Time Demand', 'Reorder Point (ROP)',
        'Maximum Stock (MAX)', 'Current Stock', 'Reserved', 'On Order',
        'Order Quantity', 'Re-Order', 'Avg Monthly Usage (AMU)',
        'Lead Time (months)', 'Safety Factor (months)', 'Review Period (months)'
    ]
    
    for row_idx, row_data in enumerate(df.itertuples(index=False), start=2):
        for col_idx, value in enumerate(row_data):
            col_name = df.columns[col_idx]
            if pd.isna(value) or value == 'N/A':
                worksheet.write(row_idx, col_idx, '', text_fmt)
            elif col_name in cost_columns:
                try:
                    worksheet.write_number(row_idx, col_idx, float(value), acct_fmt)
                except (ValueError, TypeError):
                    worksheet.write(row_idx, col_idx, str(value), text_fmt)
            elif col_name in numeric_columns:
                try:
                    worksheet.write_number(row_idx, col_idx, float(value), num_fmt)
                except (ValueError, TypeError):
                    worksheet.write(row_idx, col_idx, str(value), text_fmt)
            elif col_name == 'Description':
                worksheet.write(row_idx, col_idx, str(value), wrap_fmt)
            else:
                worksheet.write(row_idx, col_idx, str(value), text_fmt)

    # --- Column widths ---
    for col_num, col_name in enumerate(df.columns):
        if col_name == 'Code':
            worksheet.set_column(col_num, col_num, 22)
        elif col_name == 'Description':
            worksheet.set_column(col_num, col_num, 40)
        elif col_name == 'Supplier':
            worksheet.set_column(col_num, col_num, 22)
        elif col_name == 'Category':
            worksheet.set_column(col_num, col_num, 13)
        elif col_name in cost_columns:
            worksheet.set_column(col_num, col_num, 15.5)
        elif col_name in numeric_columns:
            worksheet.set_column(col_num, col_num, 11)
        else:
            base_len = df[col_name].astype(str).map(len).max() if len(df) > 0 else 10
            worksheet.set_column(col_num, col_num, min(max(base_len + 2, len(col_name) + 2), 40))

    # --- Freeze panes (freeze below row 2 = title + headers) ---
    worksheet.freeze_panes(2, 0)


def generate_report():
    try:
        print("Starting 03_generate_report.py...")
        df_final = pd.read_pickle(r"5_Archive_and_Debug\built_inventory.pkl")

        if 'Supplier' not in df_final.columns:
            df_final['Supplier'] = ''

        report_path = r"3_Live_Reports\Live_Inventory_Status.xlsx"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            temp_path = tmp.name
        
        with pd.ExcelWriter(temp_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # ═══════════════════════════════════════════════
            # DEFINE FORMATS (matching ImportStockFinal.xlsx)
            # ═══════════════════════════════════════════════
            font_name = 'Aptos Narrow'
            
            # Title row: bold, 12pt, centered
            title_fmt = workbook.add_format({
                'font_name': font_name, 'font_size': 12, 'bold': True,
                'align': 'center', 'valign': 'vcenter'
            })
            
            # Column headers: 11pt, bold, center+top, text-wrapped
            header_fmt = workbook.add_format({
                'font_name': font_name, 'font_size': 11, 'bold': True,
                'align': 'center', 'valign': 'top', 'text_wrap': True
            })
            
            # Standard text data: 11pt, top-aligned
            text_fmt = workbook.add_format({
                'font_name': font_name, 'font_size': 11,
                'valign': 'top'
            })
            
            # Numeric data: 11pt, center+top
            num_fmt = workbook.add_format({
                'font_name': font_name, 'font_size': 11,
                'align': 'center', 'valign': 'top'
            })
            
            # Accounting / ZAR currency
            acct_fmt = workbook.add_format({
                'font_name': font_name, 'font_size': 11,
                'num_format': '_-"R"* #,##0.00_-;\\-"R"* #,##0.00_-;_-"R"* "-"??_-;_-@_-',
                'align': 'center', 'valign': 'top'
            })
            
            # Wrapped text (for Description)
            wrap_fmt = workbook.add_format({
                'font_name': font_name, 'font_size': 11,
                'valign': 'top', 'text_wrap': True
            })
            
            formats = (title_fmt, header_fmt, text_fmt, num_fmt, acct_fmt, wrap_fmt)

            # ═══════════════════════════════════════════════
            # TAB 1: Master Live Inventory Status
            # ═══════════════════════════════════════════════
            ws1_name = 'Master Live Inventory Status'
            # Write a blank DataFrame to create the sheet, then format manually
            pd.DataFrame().to_excel(writer, sheet_name=ws1_name)
            ws1 = writer.sheets[ws1_name]
            apply_sheet_formatting(workbook, ws1, df_final, 
                                   'FM - Master Live Inventory Status', formats)

            # ═══════════════════════════════════════════════
            # TAB 2: Live Inventory Report
            # ═══════════════════════════════════════════════
            report_cols = [
                'Code', 'Description', 'Category', 'Supplier',
                'Safety Stock', 'Reorder Point (ROP)', 'Maximum Stock (MAX)',
                'Current Stock', 'Reserved', 'On Order', 'Re-Order'
            ]
            report_cols = [c for c in report_cols if c in df_final.columns]
            df_report = df_final[report_cols].copy()
            
            ws2_name = 'Live Inventory Report'
            pd.DataFrame().to_excel(writer, sheet_name=ws2_name)
            ws2 = writer.sheets[ws2_name]
            apply_sheet_formatting(workbook, ws2, df_report,
                                   'FM - Live Inventory Report', formats)

            # ═══════════════════════════════════════════════
            # TAB 3: Suggested Orders
            # ═══════════════════════════════════════════════
            order_cols = report_cols + ['Cost Price', 'Order Cost']
            order_cols = [c for c in order_cols if c in df_final.columns]
            df_orders = df_final[order_cols].copy()
            df_orders = df_orders[df_orders['Re-Order'] > 0].copy()
            
            ws3_name = 'Suggested Orders'
            pd.DataFrame().to_excel(writer, sheet_name=ws3_name)
            ws3 = writer.sheets[ws3_name]
            apply_sheet_formatting(workbook, ws3, df_orders,
                                   'FM - Suggested Orders', formats)

            # ═══════════════════════════════════════════════
            # TAB 4: Stock Health Summary
            # ═══════════════════════════════════════════════
            
            # 1. Total Inventory Value (Qty on Hand * Cost Price)
            df_final['Stock Item Value'] = pd.to_numeric(df_final['Current Stock'], errors='coerce').fillna(0) * pd.to_numeric(df_final['Cost Price'], errors='coerce').fillna(0)
            total_inv_value = df_final['Stock Item Value'].sum()
            
            # 2. Low Stock Count
            low_stock_mask = pd.to_numeric(df_final['Current Stock'], errors='coerce').fillna(0) < pd.to_numeric(df_final['Reorder Point (ROP)'], errors='coerce').fillna(0)
            low_stock_count = low_stock_mask.sum()
            
            # 3. Stagnant Items Count
            amu_numeric = pd.to_numeric(df_final['Avg Monthly Usage (AMU)'].replace('N/A', 0), errors='coerce').fillna(0)
            stagnant_mask = (pd.to_numeric(df_final['Current Stock'], errors='coerce').fillna(0) > 0) & (amu_numeric == 0)
            stagnant_count = stagnant_mask.sum()
            
            ws4_name = 'Stock Health'
            pd.DataFrame().to_excel(writer, sheet_name=ws4_name)
            ws4 = writer.sheets[ws4_name]
            
            ws4.merge_range(0, 0, 0, 1, 'FM - Stock Health Summary', title_fmt)
            ws4.set_row(0, 18)
            ws4.set_row(1, 43)
            ws4.write(1, 0, 'Metric', header_fmt)
            ws4.write(1, 1, 'Value', header_fmt)
            
            ws4.write(2, 0, 'Total Inventory Value', text_fmt)
            ws4.write_number(2, 1, total_inv_value, acct_fmt)
            
            ws4.write(3, 0, 'Items with Low Stock', text_fmt)
            ws4.write_number(3, 1, low_stock_count, num_fmt)
            
            ws4.write(4, 0, 'Stagnant Items (Stock > 0, AMU = 0)', text_fmt)
            ws4.write_number(4, 1, stagnant_count, num_fmt)
            
            ws4.set_column(0, 0, 35)
            ws4.set_column(1, 1, 20)

            # ═══════════════════════════════════════════════
            # TAB 5: Executive Dashboard
            # ═══════════════════════════════════════════════
            ws5_name = 'Executive Dashboard'
            pd.DataFrame().to_excel(writer, sheet_name=ws5_name)
            ws5 = writer.sheets[ws5_name]
            
            # --- KPIs ---
            total_order_value = df_orders['Order Cost'].sum()
            items_to_reorder = len(df_orders)

            ws5.merge_range(0, 0, 0, 4, 'FM - Executive Dashboard', title_fmt)
            ws5.set_row(0, 18)
            
            kpi_header = workbook.add_format({'font_name': font_name, 'font_size': 11, 'bold': True, 'align': 'center'})
            kpi_value_acct = workbook.add_format({'font_name': font_name, 'font_size': 11, 'num_format': '_-"R"* #,##0.00_-;\\-"R"* #,##0.00_-;_-"R"* "-"??_-;_-@_-', 'align': 'center'})
            kpi_value_num = workbook.add_format({'font_name': font_name, 'font_size': 11, 'align': 'center'})

            ws5.write(2, 1, 'Total Inventory Value', kpi_header)
            ws5.write(3, 1, total_inv_value, kpi_value_acct)
            ws5.write(2, 2, 'Total Value of Suggested Orders', kpi_header)
            ws5.write(3, 2, total_order_value, kpi_value_acct)
            ws5.write(2, 3, 'Number of Items to Re-Order', kpi_header)
            ws5.write(3, 3, items_to_reorder, kpi_value_num)

            # --- Chart 1: Inventory Value by Category ---
            cat_val = df_final.groupby('Category')['Stock Item Value'].sum().sort_values(ascending=False).reset_index()
            cat_val = cat_val[cat_val['Stock Item Value'] > 0]
            
            chart1_data_len = len(cat_val) + 1
            ws5.write_column('G2', cat_val['Category'])
            ws5.write_column('H2', cat_val['Stock Item Value'])
            
            chart1 = workbook.add_chart({'type': 'pie'})
            chart1.add_series({
                'name': 'Inventory Value by Category',
                'categories': f"='{ws5_name}'!$G$2:$G${chart1_data_len}",
                'values':     f"='{ws5_name}'!$H$2:$H${chart1_data_len}",
            })
            chart1.set_title({'name': 'Inventory Value by Category'})
            ws5.insert_chart('A8', chart1)

            # --- Chart 2: Top 10 Items to Re-Order by Value ---
            top_10_orders = df_orders.nlargest(10, 'Order Cost')
            ws5.write_column('J2', top_10_orders['Description'])
            ws5.write_column('K2', top_10_orders['Order Cost'])

            chart2 = workbook.add_chart({'type': 'bar'})
            chart2.add_series({
                'name': 'Top 10 Items to Re-Order',
                'categories': f"='{ws5_name}'!$J$2:$J$11",
                'values':     f"='{ws5_name}'!$K$2:$K$11",
            })
            chart2.set_title({'name': 'Top 10 Items to Re-Order by Value'})
            chart2.set_legend({'position': 'none'})
            ws5.insert_chart('A24', chart2)
            
            # --- Chart 3: Stock Status Breakdown ---
            status_counts = df_final['Stock Status'].value_counts()
            ws5.write_column('M2', status_counts.index)
            ws5.write_column('N2', status_counts.values)

            chart3 = workbook.add_chart({'type': 'pie'})
            chart3.add_series({
                'name': 'Stock Status Breakdown',
                'categories': f"='{ws5_name}'!$M$2:$M$4",
                'values':     f"='{ws5_name}'!$N$2:$N$4",
            })
            chart3.set_title({'name': 'Stock Status Breakdown'})
            ws5.insert_chart('H24', chart3)

            # ═══════════════════════════════════════════════
            # TAB 6: Stock Take
            # ═══════════════════════════════════════════════
            st_cols = ['Code', 'Description', 'Category', 'Bin', 'Current Stock', 'Reserved']
            st_cols = [c for c in st_cols if c in df_final.columns]
            df_st = df_final[st_cols].copy()
            
            ws6_name = 'Stock Take'
            pd.DataFrame().to_excel(writer, sheet_name=ws6_name)
            ws6 = writer.sheets[ws6_name]
            apply_sheet_formatting(workbook, ws6, df_st,
                                   'FM - Stock Take', formats)

            # ═══════════════════════════════════════════════
            # TAB 7: Bin Locations
            # ═══════════════════════════════════════════════
            bin_loc_path = r"5_Archive_and_Debug\extracted_bin_locations.pkl"
            if os.path.exists(bin_loc_path):
                df_bins = pd.read_pickle(bin_loc_path)
                ws7_name = 'Bin Locations'
                pd.DataFrame().to_excel(writer, sheet_name=ws7_name)
                ws7 = writer.sheets[ws7_name]
                apply_sheet_formatting(workbook, ws7, df_bins[['Bin Code']],
                                       'FM - Bin Locations', formats)

        # Move to final location
        try:
            shutil.move(temp_path, report_path)
            print(f"  Successfully generated 5-tab report at {report_path}")
        except PermissionError:
            shutil.move(temp_path, r"5_Archive_and_Debug\Latest_Report.xlsx")
            log_error(f"Locked File - saved backup to Archive: {report_path} currently open.")
            exit(1)
            
    except Exception as e:
        err_msg = f"03_generate_report failed: {str(e)}\n{traceback.format_exc()}"
        log_error(err_msg)
        exit(1)

if __name__ == "__main__":
    generate_report()
