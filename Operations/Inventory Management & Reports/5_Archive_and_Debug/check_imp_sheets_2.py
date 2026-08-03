import pandas as pd
with open(r'5_Archive_and_Debug\cols3.txt', 'w', encoding='utf-8') as f:
    excel_path = '2_Source_Data/ImportStockFinal.xlsx'
    with pd.ExcelFile(excel_path) as xls:
        for sheet in ['ImportStockCount_TOT', 'FPZ']:
            if sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet, nrows=5)
                f.write(f"\n--- Sheet: {sheet} ---\n")
                f.write("Columns: " + str(df.columns.tolist()) + "\n")
                f.write("Data snippet:\n")
                f.write(str(df.head(2).to_dict('records')) + "\n")
