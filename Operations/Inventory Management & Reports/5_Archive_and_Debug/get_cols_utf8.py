import pandas as pd
with open(r'5_Archive_and_Debug\import_cols.txt', 'w', encoding='utf-8') as f:
    df = pd.read_excel('2_Source_Data/ImportStockFinal.xlsx', nrows=5)
    f.write("Columns:\n")
    for col in df.columns:
        f.write(f"- {col}\n")
    f.write("\nData dict:\n")
    f.write(str(df.head(1).to_dict('records')))
