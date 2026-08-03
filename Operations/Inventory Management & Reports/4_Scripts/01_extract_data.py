import pandas as pd
import tempfile
import shutil
import os
import traceback
from datetime import datetime

def log_error(msg):
    with open(r"1_Documentation\GEMINI.md", "a", encoding="utf-8") as f:
        f.write(f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {msg}\n")
    print(f"ERROR: {msg}")

def extract_data():
    try:
        print("Starting 01_extract_data.py...")
        # 1. Extract ItemListingReport.csv
        csv_path = r"2_Source_Data\ItemListingReport.csv"
        try:
            df_csv = pd.read_csv(csv_path, skiprows=1, encoding='utf-8-sig', on_bad_lines='skip')
        except Exception as e:
            df_csv = pd.read_csv(csv_path, skiprows=1, encoding='latin1', on_bad_lines='skip')
        
        if 'Code' not in df_csv.columns:
            raise ValueError("CSV missing 'Code' column.")
            
        df_csv.to_pickle(r"5_Archive_and_Debug\extracted_items.pkl")
        print("Successfully extracted ItemListingReport.csv")

        # 2. Extract Workshop Stock
        xlsx_path = r"2_Source_Data\Workshop Stock 19.03.26.xlsx"
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            temp_path = tmp.name
        
        try:
            shutil.copy2(xlsx_path, temp_path)
            # Main calculation sheet
            df_xlsx = pd.read_excel(temp_path, sheet_name='W-shop Calc')
            # Extract the embedded reference sheet using its known name or fallback to ItemListingReport
            try:
                df_ref = pd.read_excel(temp_path, sheet_name='ItemListingReport')
                df_ref.to_pickle(r"5_Archive_and_Debug\extracted_ws_ref.pkl")
            except Exception as inner_e:
                print("Warning: ItemListingReport sheet not found in Workshop Stock.", inner_e)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        if 'Code' not in df_xlsx.columns:
            raise ValueError("XLSX missing 'Code' column.")
            
        df_xlsx.to_pickle(r"5_Archive_and_Debug\extracted_workshop.pkl")
        print("Successfully extracted Workshop Stock 19.03.26.xlsx")

        # 3. Extract ImportStockFinal
        imp_path = r"2_Source_Data\ImportStockFinal.xlsx"
        if os.path.exists(imp_path):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                temp_imp_path = tmp.name
            try:
                shutil.copy2(imp_path, temp_imp_path)
                # The data table starts on row 1 (0-indexed)
                df_imp = pd.read_excel(temp_imp_path, sheet_name='ImportStockCount_TOT', skiprows=1)
                # Rename 'Item' to 'Code' for easier joining
                if 'Item' in df_imp.columns:
                    df_imp.rename(columns={'Item': 'Code'}, inplace=True)
                df_imp.to_pickle(r"5_Archive_and_Debug\extracted_import_final.pkl")
                print("Successfully extracted ImportStockFinal.xlsx")
            finally:
                if os.path.exists(temp_imp_path):
                    os.remove(temp_imp_path)
        else:
            print("Notice: ImportStockFinal.xlsx not found.")

        # 4. Extract Cost Prices
        cost_path = r"2_Source_Data\Cost Prices.xlsx"
        if os.path.exists(cost_path):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                temp_cost_path = tmp.name
            try:
                shutil.copy2(cost_path, temp_cost_path)
                df_cost = pd.read_excel(temp_cost_path, sheet_name='Cost Prices')
                # Normalise column names
                df_cost.columns = [c.strip() for c in df_cost.columns]
                if 'Stock Code' in df_cost.columns:
                    df_cost.rename(columns={'Stock Code': 'Code'}, inplace=True)
                df_cost.dropna(subset=['Code'], inplace=True)
                df_cost['Code'] = df_cost['Code'].astype(str).str.strip()
                df_cost.to_pickle(r"5_Archive_and_Debug\extracted_cost_prices.pkl")
                print(f"Successfully extracted Cost Prices.xlsx ({len(df_cost)} rows)")
            finally:
                if os.path.exists(temp_cost_path):
                    os.remove(temp_cost_path)
        # 5. Extract Outstanding PO Suppliers
        po_csv_path = r"2_Source_Data\OutstandingPurchaseOrdersBySupplierReport.csv"
        if os.path.exists(po_csv_path):
            import csv
            supplier_mapping = {}
            with open(po_csv_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                current_supplier = None
                for row in reader:
                    if not row or not any(row): continue
                    while len(row) < 5: row.append("")
                    c0, c1, c2, c3, c4 = row[0], row[1], row[2], row[3], row[4]
                    if c0 and not c1 and not c2 and "Total" not in c0 and "Page" not in c0 and "Date" not in c0 and "Name" not in c0 and "Fan Move" not in c0 and "Supplier" not in c0:
                        current_supplier = c0.strip()
                        continue
                    if not c0 and not c1 and not c2 and not c3:
                        desc = c4.strip()
                        if " - " in desc:
                            item_code = desc.split(" - ")[0].strip()
                            if item_code and current_supplier:
                                if item_code not in supplier_mapping:
                                    supplier_mapping[item_code] = current_supplier
            pd.Series(supplier_mapping).to_pickle(r"5_Archive_and_Debug\po_supplier_intelligence.pkl")
            print(f"Successfully extracted Outstanding PO Suppliers ({len(supplier_mapping)} mappings)")
        else:
            print("Notice: OutstandingPurchaseOrdersBySupplierReport.csv not found.")

        # 6. Extract Stock Take Overrides
        live_repo_path = r"3_Live_Reports\Live_Inventory_Status.xlsx"
        if os.path.exists(live_repo_path):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                temp_live_path = tmp.name
            try:
                shutil.copy2(live_repo_path, temp_live_path)
                df_st = pd.read_excel(temp_live_path, sheet_name='Stock Take', skiprows=1)
                if 'Code' in df_st.columns:
                    df_st['Code'] = df_st['Code'].astype(str).str.strip()
                    df_st.dropna(subset=['Code'], inplace=True)
                    df_st.to_pickle(r"5_Archive_and_Debug\stock_take_overrides.pkl")
                    print(f"Successfully extracted Stock Take overrides ({len(df_st)} rows)")
                else:
                    print("Notice: 'Code' column missing in Stock Take.")
            except Exception as e:
                print(f"Notice: Stock Take sheet not found or unreadable in live report. ({e})")
            finally:
                if os.path.exists(temp_live_path):
                    os.remove(temp_live_path)

        # 7. Extract Bin Locations
        bin_path = r"2_Source_Data\Stores locations.xlsx"
        if os.path.exists(bin_path):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                temp_bin_path = tmp.name
            try:
                shutil.copy2(bin_path, temp_bin_path)
                df_bins = pd.read_excel(temp_bin_path)
                df_bins.dropna(how='all', inplace=True)
                
                # Create a composite Bin Code
                df_bins['Row#'] = df_bins['Row#'].astype(str).str.replace(r'\.0$', '', regex=True)
                df_bins['Racks'] = df_bins['Racks'].astype(str).str.replace(r'\.0$', '', regex=True)
                df_bins['Bins'] = df_bins['Bins'].astype(str).str.replace(r'\.0$', '', regex=True)
                
                store_map = {'Main Store': 'MS', 'Up Stairs': 'US'}
                df_bins['Store Code'] = df_bins['Stores Locations'].str.strip().map(store_map).fillna('XX')
                
                df_bins['Bin Code'] = df_bins['Store Code'] + '-RW' + \
                                      df_bins['Row#'].str.strip() + '-RCK' + \
                                      df_bins['Racks'].str.strip() + '-B' + \
                                      df_bins['Bins'].str.strip()

                df_bins.to_pickle(r"5_Archive_and_Debug\extracted_bin_locations.pkl")
                print(f"Successfully extracted Bin Locations ({len(df_bins)} rows)")
            finally:
                if os.path.exists(temp_bin_path):
                    os.remove(temp_bin_path)

    except Exception as e:
        err_msg = f"01_extract_data failed: {str(e)}\n{traceback.format_exc()}"
        log_error(err_msg)
        exit(1)

if __name__ == "__main__":
    extract_data()
