import pandas as pd
with open(r'5_Archive_and_Debug\cols2.txt', 'w', encoding='utf-8') as f:
    df = pd.read_excel('2_Source_Data/ImportStockFinal.xlsx', nrows=50)
    for idx, row in df.iterrows():
        f.write(f"{idx}: {row.dropna().to_dict()}\n")
