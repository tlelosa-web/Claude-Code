import pandas as pd
df = pd.read_excel('3_Live_Reports/Live_Inventory_Status.xlsx')
print(df.columns)
print("Total rows:", len(df))
print(df[['Code', 'Category', 'Supplier', 'Cost Price']].head())

with open('5_Archive_and_Debug/output_test.txt', 'w') as f:
    f.write(str(df.columns.tolist()) + "\n")
    f.write(f"Total rows: {len(df)}\n")
    f.write(str(df[['Code', 'Category', 'Supplier', 'Cost Price']].head()) + "\n")
