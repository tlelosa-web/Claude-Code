import pandas as pd
excel_file = pd.ExcelFile(r'2_Source_Data\Workshop Stock 19.03.26.xlsx')
print("Sheet names in Workshop Stock:")
print(excel_file.sheet_names)
