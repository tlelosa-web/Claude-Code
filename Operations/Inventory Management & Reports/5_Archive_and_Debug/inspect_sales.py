import pandas as pd

with open(r'5_Archive_and_Debug\sales_cols.txt', 'w', encoding='utf-8') as f:
    # This is a SAGE export with sep=, on row 0 and merged header rows.
    # The actual headers seem to span rows 1-3. Let's try skiprows=1 first
    try:
        df = pd.read_csv(r'2_Source_Data\CustomerSalesOrdersByCustomer.csv', 
                         skiprows=1, encoding='utf-8-sig', on_bad_lines='skip')
        f.write("With skiprows=1:\n")
        f.write(f"Columns: {df.columns.tolist()}\n")
        f.write(f"Shape: {df.shape}\n\n")
        for idx, row in df.head(15).iterrows():
            f.write(f"{idx}: {row.dropna().to_dict()}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
    
    f.write("\n\n--- Alternative: skiprows=3 ---\n")
    try:
        df2 = pd.read_csv(r'2_Source_Data\CustomerSalesOrdersByCustomer.csv', 
                          skiprows=3, encoding='utf-8-sig', on_bad_lines='skip')
        f.write(f"Columns: {df2.columns.tolist()}\n")
        f.write(f"Shape: {df2.shape}\n\n")
        for idx, row in df2.head(15).iterrows():
            f.write(f"{idx}: {row.dropna().to_dict()}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
