import pandas as pd
xls = pd.ExcelFile('2_Source_Data/ImportStockFinal.xlsx')
print(xls.sheet_names)
