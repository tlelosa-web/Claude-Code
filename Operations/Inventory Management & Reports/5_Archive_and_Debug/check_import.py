import pandas as pd

try:
    df = pd.read_excel('2_Source_Data/ImportStockFinal.xlsx', nrows=5)
    print("Columns:", df.columns.tolist())
    print("Data:", df.head(1).to_dict('records'))
except Exception as e:
    print("Error:", e)
