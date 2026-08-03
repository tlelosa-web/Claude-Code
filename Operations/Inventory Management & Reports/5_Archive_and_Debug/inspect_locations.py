import pandas as pd
try:
    df = pd.read_excel(r'2_Source_Data\Stores locations.xlsx')
    print(df.to_string())
except Exception as e:
    print(e)
