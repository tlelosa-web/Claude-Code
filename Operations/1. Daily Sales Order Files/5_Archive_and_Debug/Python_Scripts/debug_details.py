
import pandas as pd
import openpyxl
from update_sales_report import load_contract_details

def debug_details_update():
    print("Loading Contract Details...")
    details = load_contract_details()
    
    # Check if specific SO numbers or Job numbers are in the keys
    # The user provided SO4448 and SO4452.
    # The current logic keys off 'Job Number'.
    # If Job Number is missing (blank), it won't find a match.
    
    print(f"\nTotal Contracts Loaded: {len(details)}")
    
    # Copy to temp file to read
    # import shutil
    # shutil.copy("Sales Order Report - 03.2026.xlsx", "temp_debug.xlsx")
    # wb = openpyxl.load_workbook("temp_debug.xlsx", data_only=True)
    # ws = wb["16.03.2026"]
    
    # Just print the details to verify loading
    print(f"Details for SO4448: {details.get('SO4448', 'Not Found')}")
    print(f"Details for SO4452: {details.get('SO4452', 'Not Found')}")
    
    # Inspect Register Columns for SO Number
    print("\nInspecting Register Columns for SO Number:")
    reg_file = "Contract register 2026 - 16.03.23.xlsx"
    df = pd.read_excel(reg_file, header=3)
    
    print("\nSearching for SO4448/SO4452 in Register:")
    for term in ["SO4448", "SO4452", "61713"]:
        # Search in all columns
        mask = df.apply(lambda x: x.astype(str).str.contains(term, case=False, na=False)).any(axis=1)
        if mask.any():
            print(f"Found {term} in Register!")
            # Print the full row to see which column it is in
            print(df[mask])
        else:
            print(f"{term} NOT found in Register.")
    
    return

if __name__ == "__main__":
    debug_details_update()
