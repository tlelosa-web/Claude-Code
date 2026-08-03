"""Test parsing of item 11127 specifically."""

import csv
from datetime import datetime

def parse_date(s):
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

SOURCE_CSV = "2_Source_Data/ItemMovementReport.csv"

print("Testing parsing of lines around item 11127...")
print("=" * 70)

with open(SOURCE_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    next(reader)  # Skip title
    for _ in range(3):
        try:
            next(reader)
        except StopIteration:
            break
    
    line_num = 4
    current_item_code = ""
    
    for row in reader:
        line_num += 1
        if line_num < 1465 or line_num > 1470:
            continue
            
        if not row or not row[0].strip():
            continue
        
        first = row[0].strip()
        print(f"\nLine {line_num}: '{first}'")
        
        if first.lower().startswith("total for item:"):
            print(f"  -> Total line, clearing current_item_code")
            current_item_code = ""
            continue
        
        dt = parse_date(first)
        print(f"  -> Parsed as date: {dt}")
        
        if dt and len(row) >= 5:
            desc = row[2].strip()
            is_purchase = desc == "Supplier Invoice"
            is_sale = desc == "Tax Invoice"
            print(f"  -> TRANSACTION: desc='{desc}', is_purchase={is_purchase}, is_sale={is_sale}")
            print(f"  -> Item code: '{current_item_code}'")
        else:
            print(f"  -> ITEM HEADER")
            current_item_code = first
            if " - " in first:
                parts = first.split(" - ", 1)
                current_item_code = parts[0].strip()
                desc_raw = parts[1].strip()
                print(f"  -> Extracted code: '{current_item_code}', desc: '{desc_raw}'")
