import pandas as pd

df = pd.read_pickle(r'5_Archive_and_Debug\built_inventory.pkl')
print("Total Items:", len(df))
print("Items with Cost Price null:", df['Cost Price'].isna().sum())
print("Items with Category null:", df['Category'].isna().sum())

# Let's see some from Workshop Stock
df_ws = pd.read_pickle(r'5_Archive_and_Debug\extracted_workshop.pkl')
print("\nWorkshop Items:", len(df_ws))
ws_codes = df_ws['Code'].astype(str).str.strip().tolist()
df_ws_in_merged = df[df['Code'].isin(ws_codes)]
print("Workshop Items in Merged:", len(df_ws_in_merged))
print("Workshop Items in Merged with Cost Price null:", df_ws_in_merged['Cost Price'].isna().sum())
print("Workshop Items in Merged with Category null:", df_ws_in_merged['Category'].isna().sum())

print("\nSample of Workshop Items in Merged:")
print(df_ws_in_merged[['Code', 'Description', 'Category', 'Cost Price']].head())
