
import openpyxl

file_path = "Sales Order Report - 03.2026.xlsx"
wb = openpyxl.load_workbook(file_path)

sheets_to_delete = ["17.03.2026"]
for sheet in sheets_to_delete:
    if sheet in wb.sheetnames:
        print(f"Deleting {sheet}")
        del wb[sheet]

wb.save(file_path)
print("Cleanup complete.")
