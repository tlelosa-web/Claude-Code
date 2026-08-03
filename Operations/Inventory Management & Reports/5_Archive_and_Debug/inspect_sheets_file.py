import pandas as pd

excel_path = r'2_Source_Data\Workshop Stock 19.03.26.xlsx'
with open(r'5_Archive_and_Debug\sheet_cols.txt', 'w') as f:
    with pd.ExcelFile(excel_path) as xls:
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
            f.write(f"\n--- Sheet: {sheet} ---\n")
            f.write("Columns: " + str(df.columns.tolist()) + "\n")
