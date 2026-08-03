import pandas as pd

df_workshop = pd.read_pickle(r'5_Archive_and_Debug\extracted_workshop.pkl')
df_sage = pd.read_pickle(r'5_Archive_and_Debug\extracted_items.pkl')

ws_codes = df_workshop['Code'].astype(str).str.strip().tolist()
sage_codes = df_sage['Code'].astype(str).str.strip().tolist()

matched = set(ws_codes).intersection(set(sage_codes))

with open(r'5_Archive_and_Debug\join_stats.txt', 'w') as f:
    f.write(f"Workshop total: {len(ws_codes)}\n")
    f.write(f"Sage total: {len(sage_codes)}\n")
    f.write(f"Matched directly: {len(matched)}\n\n")

    ws_upper = [c.upper() for c in ws_codes]
    sage_upper = [c.upper() for c in sage_codes]
    matched_upper = set(ws_upper).intersection(set(sage_upper))
    f.write(f"Matched Upper: {len(matched_upper)}\n\n")
    
    # Let's peek at a few codes
    f.write(f"Workshop sample: {ws_codes[:5]}\n")
    f.write(f"Sage sample: {sage_codes[:5]}\n")
