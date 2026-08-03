import pandas as pd
import numpy as np
import traceback
from datetime import datetime
import os

def log_error(msg):
    with open(r"1_Documentation\GEMINI.md", "a", encoding="utf-8") as f:
        f.write(f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR: {msg}\n")
    print(f"ERROR: {msg}")

def build_inventory():
    try:
        print("Starting 02_build_inventory.py...")
        df_workshop = pd.read_pickle(r"5_Archive_and_Debug\extracted_workshop.pkl")
        df_items = pd.read_pickle(r"5_Archive_and_Debug\extracted_items.pkl")

        # Clean 'Code'
        df_workshop['Code'] = df_workshop['Code'].astype(str).str.strip()
        df_items['Code'] = df_items['Code'].astype(str).str.strip()

        df_items['Qty on Hand'] = pd.to_numeric(df_items['Qty on Hand'], errors='coerce').fillna(0)
        
        df_sage = df_items[['Code', 'Description', 'Category', 'Qty on Hand']].copy()
        
        # Outer merge all SAGE items
        df_merged = pd.merge(df_workshop, df_sage, on='Code', how='outer', suffixes=('', '_sage'))
        
        df_merged['Description'] = df_merged['Description'].fillna(df_merged['Description_sage'])
        df_merged['Category'] = df_merged['Category'].fillna(df_merged['Category_sage'])
        df_merged['Current Stock'] = df_merged['Qty on Hand'].fillna(df_merged['Current Stock'])
        df_merged.drop(columns=['Description_sage', 'Category_sage', 'Qty on Hand'], inplace=True)

        # --- Fill from Workshop Stock reference sheet ---
        ref_path = r"5_Archive_and_Debug\extracted_ws_ref.pkl"
        if os.path.exists(ref_path):
            df_ref = pd.read_pickle(ref_path)
            df_ref['Code'] = df_ref['Code'].astype(str).str.strip()
            cat_map = dict(zip(df_ref['Code'], df_ref['Category']))
            df_merged['Category'] = df_merged['Category'].fillna(df_merged['Code'].map(cat_map))
            cost_col = 'Cost Price' if 'Cost Price' in df_ref.columns else 'Last Cost'
            if cost_col in df_ref.columns:
                cost_map = dict(zip(df_ref['Code'], pd.to_numeric(df_ref[cost_col], errors='coerce')))
                df_merged['Cost Price'] = df_merged['Cost Price'].fillna(df_merged['Code'].map(cost_map))
        
        # --- Fill from ImportStockFinal ---
        imp_ref_path = r"5_Archive_and_Debug\extracted_import_final.pkl"
        if os.path.exists(imp_ref_path):
            df_imp = pd.read_pickle(imp_ref_path)
            df_imp['Code'] = df_imp['Code'].astype(str).str.strip()
            
            if 'Supplier' not in df_merged.columns:
                df_merged['Supplier'] = None

            if 'Category' in df_imp.columns:
                imp_cat_map = dict(zip(df_imp['Code'], df_imp['Category']))
                df_merged['Category'] = df_merged['Category'].fillna(df_merged['Code'].map(imp_cat_map))
            if 'Cost Price' in df_imp.columns:
                imp_cost_map = dict(zip(df_imp['Code'], pd.to_numeric(df_imp['Cost Price'], errors='coerce')))
                df_merged['Cost Price'] = df_merged['Cost Price'].fillna(df_merged['Code'].map(imp_cost_map))
            if 'Supplier' in df_imp.columns:
                imp_sup_map = dict(zip(df_imp['Code'], df_imp['Supplier']))
                df_merged['Supplier'] = df_merged['Supplier'].fillna(df_merged['Code'].map(imp_sup_map))

        # === INJECT COST PRICES FILE (Secondary fallback for Cost, Supplier, Category) ===
        if 'Supplier' not in df_merged.columns:
            df_merged['Supplier'] = None
            
        cost_path = r"5_Archive_and_Debug\extracted_cost_prices.pkl"
        if os.path.exists(cost_path):
            df_cost = pd.read_pickle(cost_path)
            df_cost['Code'] = df_cost['Code'].astype(str).str.strip()
            cost_fills = 0
            if 'Cost Price' in df_cost.columns:
                cost_map = dict(zip(df_cost['Code'], pd.to_numeric(df_cost['Cost Price'], errors='coerce')))
                before = df_merged['Cost Price'].isna().sum()
                df_merged['Cost Price'] = df_merged['Cost Price'].fillna(df_merged['Code'].map(cost_map))
                cost_fills = before - df_merged['Cost Price'].isna().sum()
            if 'Supplier' in df_cost.columns:
                sup_map = dict(zip(df_cost['Code'], df_cost['Supplier']))
                df_merged['Supplier'] = df_merged['Supplier'].fillna(df_merged['Code'].map(sup_map))
            if 'Category' in df_cost.columns:
                cat_map = dict(zip(df_cost['Code'], df_cost['Category']))
                df_merged['Category'] = df_merged['Category'].fillna(df_merged['Code'].map(cat_map))
            print(f"  Cost Prices fallback: {cost_fills} cost prices filled.")

        # === INJECT PO SUPPLIER INTELLIGENCE (Tertiary fallback) ===
        po_intel_path = r"5_Archive_and_Debug\po_supplier_intelligence.pkl"
        if os.path.exists(po_intel_path):
            po_intel = pd.read_pickle(po_intel_path)
            df_merged['Supplier'] = df_merged['Supplier'].fillna(df_merged['Code'].map(po_intel))

        # === INFER MISSING CATEGORIES FROM SUPPLIER ===
        mask_has_cat = df_merged['Category'].notna() & (df_merged['Category'] != '') & (df_merged['Category'] != 'N/A')
        if mask_has_cat.any() and df_merged['Supplier'].notna().any():
            sup_cat = df_merged[mask_has_cat].groupby('Supplier')['Category'].agg(lambda x: x.mode()[0] if not x.mode().empty else np.nan)
            df_merged['Category'] = df_merged['Category'].fillna(df_merged['Supplier'].map(sup_cat))

        # === INJECT AMU (Dual Source) ===
        amu_path = r"5_Archive_and_Debug\amu_lookup.pkl"
        po_amu_path = r"5_Archive_and_Debug\amu_po_lookup.pkl"
        if os.path.exists(amu_path):
            sales_amu = pd.read_pickle(amu_path)
            df_merged['Avg Monthly Usage (AMU)'] = df_merged['Description'].map(sales_amu)
            sales_hit = df_merged['Avg Monthly Usage (AMU)'].notna().sum()
            if os.path.exists(po_amu_path):
                po_amu = pd.read_pickle(po_amu_path)
                mask = df_merged['Avg Monthly Usage (AMU)'].isna()
                df_merged.loc[mask, 'Avg Monthly Usage (AMU)'] = df_merged.loc[mask, 'Code'].map(po_amu)
                po_hit = df_merged['Avg Monthly Usage (AMU)'].notna().sum() - sales_hit
                print(f"  AMU mapped: {sales_hit} from sales, {po_hit} from PO fallback.")
        else:
            if 'Avg Monthly Usage (AMU)' not in df_merged.columns:
                df_merged['Avg Monthly Usage (AMU)'] = np.nan

        # === INJECT LEAD TIME (from PO) ===
        lt_path = r"5_Archive_and_Debug\po_leadtime_lookup.pkl"
        if os.path.exists(lt_path):
            po_lt = pd.read_pickle(lt_path)
            if 'Lead Time (months)' in df_merged.columns:
                df_merged['Lead Time (months)'] = df_merged['Code'].map(po_lt).fillna(df_merged['Lead Time (months)'])
            else:
                df_merged['Lead Time (months)'] = df_merged['Code'].map(po_lt)
            lt_count = df_merged['Lead Time (months)'].notna().sum()
            print(f"  Lead Time mapped: {lt_count} items.")
        
        # === INJECT STOCK TAKE OVERRIDES & CLEANUP NEGATIVE STOCK ===
        df_merged['Reserved'] = 0.0
        st_path = r"5_Archive_and_Debug\stock_take_overrides.pkl"
        if os.path.exists(st_path):
            df_st = pd.read_pickle(st_path)
            if 'Current Stock' in df_st.columns:
                st_stock = {k: v for k, v in dict(zip(df_st['Code'], pd.to_numeric(df_st['Current Stock'], errors='coerce'))).items() if pd.notna(v)}
                df_merged['Current Stock'] = df_merged['Code'].map(st_stock).fillna(df_merged['Current Stock'])
            if 'Reserved' in df_st.columns:
                st_res = {k: v for k, v in dict(zip(df_st['Code'], pd.to_numeric(df_st['Reserved'], errors='coerce'))).items() if pd.notna(v)}
                df_merged['Reserved'] = df_merged['Code'].map(st_res).fillna(0.0)

        df_merged['Current Stock'] = pd.to_numeric(df_merged['Current Stock'], errors='coerce').fillna(0)
        df_merged['Reserved'] = pd.to_numeric(df_merged['Reserved'], errors='coerce').fillna(0)
        df_merged.loc[(df_merged['Current Stock'] < 0) & (df_merged['Reserved'] == 0), 'Current Stock'] = 0

        # === RECALCULATE STOCK LEVELS ===
        # Convert AMU and Lead Time to numeric (N/A -> NaN)
        df_merged['Avg Monthly Usage (AMU)'] = pd.to_numeric(df_merged['Avg Monthly Usage (AMU)'], errors='coerce')
        df_merged['Lead Time (months)'] = pd.to_numeric(df_merged['Lead Time (months)'], errors='coerce')
        df_merged['Current Stock'] = pd.to_numeric(df_merged['Current Stock'], errors='coerce').fillna(0)
        df_merged['On Order'] = pd.to_numeric(df_merged['On Order'], errors='coerce').fillna(0)

        # Safety Factor and Review Period defaults if not present
        if 'Safety Factor (months)' not in df_merged.columns:
            df_merged['Safety Factor (months)'] = 1.0
        df_merged['Safety Factor (months)'] = pd.to_numeric(df_merged['Safety Factor (months)'], errors='coerce').fillna(1.0)

        if 'Review Period (months)' not in df_merged.columns:
            df_merged['Review Period (months)'] = 1.0
        df_merged['Review Period (months)'] = pd.to_numeric(df_merged['Review Period (months)'], errors='coerce').fillna(1.0)

        # Where AMU and Lead Time are available, recalculate
        has_data = df_merged['Avg Monthly Usage (AMU)'].notna() & df_merged['Lead Time (months)'].notna()

        # Safety Stock = AMU * Safety Factor
        df_merged.loc[has_data, 'Safety Stock'] = (
            df_merged.loc[has_data, 'Avg Monthly Usage (AMU)'] *
            df_merged.loc[has_data, 'Safety Factor (months)']
        ).round(0)

        # Lead Time Demand = AMU * Lead Time
        df_merged.loc[has_data, 'Lead Time Demand'] = (
            df_merged.loc[has_data, 'Avg Monthly Usage (AMU)'] *
            df_merged.loc[has_data, 'Lead Time (months)']
        ).round(0)

        # Reorder Point (ROP) = Safety Stock + Lead Time Demand
        df_merged.loc[has_data, 'Reorder Point (ROP)'] = (
            df_merged.loc[has_data, 'Safety Stock'] +
            df_merged.loc[has_data, 'Lead Time Demand']
        ).round(0)

        # Maximum Stock (MAX) = ROP + (AMU * Review Period)
        df_merged.loc[has_data, 'Maximum Stock (MAX)'] = (
            df_merged.loc[has_data, 'Reorder Point (ROP)'] +
            df_merged.loc[has_data, 'Avg Monthly Usage (AMU)'] *
            df_merged.loc[has_data, 'Review Period (months)']
        ).round(0)

        # Clean remaining numeric fields
        for col in ['Safety Stock', 'Lead Time Demand', 'Reorder Point (ROP)', 'Maximum Stock (MAX)']:
            df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce').fillna(0)

        # Order Quantity
        def calc_order(row):
            if row['Current Stock'] <= row['Reorder Point (ROP)']:
                qty = row['Maximum Stock (MAX)'] - (row['Current Stock'] - row['Reserved']) - row['On Order']
                return qty if qty > 0 else 0
            return 0
        df_merged['Order Quantity'] = df_merged.apply(calc_order, axis=1)

        # Re-Order should respect ROP threshold (same as Order Quantity)
        df_merged['Re-Order'] = df_merged['Order Quantity']

        # Cost Price cleanup
        df_merged['Cost Price'] = pd.to_numeric(df_merged['Cost Price'], errors='coerce')

        # Order Cost = Re-Order * Cost Price
        df_merged['Order Cost'] = (df_merged['Re-Order'] * df_merged['Cost Price']).round(2)

        # Fill placeholder for display columns
        df_merged['Avg Monthly Usage (AMU)'] = df_merged['Avg Monthly Usage (AMU)'].fillna('N/A')
        df_merged['Lead Time (months)'] = df_merged['Lead Time (months)'].fillna('N/A')

        # === ADD STOCK STATUS COLUMN ===
        df_merged['Stock Status'] = 'Healthy'
        df_merged.loc[df_merged['Current Stock'] > df_merged['Maximum Stock (MAX)'], 'Stock Status'] = 'Overstocked'
        df_merged.loc[df_merged['Current Stock'] <= df_merged['Reorder Point (ROP)'], 'Stock Status'] = 'Under ROP'

        # === ADD PLACEHOLDER BIN COLUMN ===
        df_merged['Bin'] = ''

        # Save
        df_merged.to_pickle(r"5_Archive_and_Debug\built_inventory.pkl")
        
        with open(r"5_Archive_and_Debug\debug_output_utf8.txt", "w", encoding="utf-8") as f:
            f.write("Inventory Build Successful.\n")
            f.write(f"Processed {len(df_merged)} total items.\n")
            f.write(f"Items missing Cost Price: {df_merged['Cost Price'].isna().sum()}\n")
            f.write(f"Items with recalculated stock levels: {has_data.sum()}\n")
            
        print(f"  Successfully built inventory: {len(df_merged)} items, {has_data.sum()} stock levels recalculated.")

    except Exception as e:
        err_msg = f"02_build_inventory failed: {str(e)}\n{traceback.format_exc()}"
        log_error(err_msg)
        exit(1)

if __name__ == "__main__":
    build_inventory()
