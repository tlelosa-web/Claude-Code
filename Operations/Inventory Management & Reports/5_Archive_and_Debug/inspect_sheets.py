import pandas as pd

excel_path = r'2_Source_Data\Workshop Stock 19.03.26.xlsx'
with pd.ExcelFile(excel_path) as xls:
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
        print(f"\n--- Sheet: {sheet} ---")
        print("Total Rows (approx):", xls.book[sheet].max_row if hasattr(xls.book, sheet) else "N/A")
        print("Columns:", df.columns.tolist())
