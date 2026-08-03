import pandas as pd

df = pd.read_excel('3_Live_Reports/Live_Inventory_Status.xlsx')

dup = df[df['Code'].duplicated(keep=False)].sort_values('Code')
print("Total duplicate codes:", len(dup))
print(dup[['Code', 'Category', 'Cost Price', 'Current Stock']].head(10))

# Try fuzzy match or upper matching
print("\nIf we uppercase, duplicates:", len(df[df['Code'].str.upper().duplicated(keep=False)]))
print("\nItems with Cost Price NaN:", df['Cost Price'].isna().sum())
print("Items with Category NaN:", df['Category'].isna().sum())
