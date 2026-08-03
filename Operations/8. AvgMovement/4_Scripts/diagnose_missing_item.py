"""Diagnostic script to check why item 11127 is missing from reports."""

import csv
from collections import defaultdict

SOURCE_CSV = "2_Source_Data/ItemMovementReport.csv"
ITEM_LISTING_CSV = "2_Source_Data/ItemListingReport.csv"

print("=" * 70)
print("DIAGNOSTIC: Why is item 11127 missing from reports?")
print("=" * 70)

# Check ItemListingReport
print("\n1. Checking ItemListingReport.csv...")
with open(ITEM_LISTING_CSV, "r", encoding="utf-8-sig") as f:
    first_line = f.readline().strip()
    if first_line.startswith("sep="):
        print(f"   Found sep= directive: {first_line}")
    
    reader = csv.DictReader(f)
    listing_found = False
    for row in reader:
        code = row.get("Code", "").strip()
        if code == "11127":
            listing_found = True
            print(f"   [OK] Item 11127 FOUND in ItemListingReport:")
            print(f"     - Description: {row.get('Description', '')}")
            print(f"     - Category: {row.get('Category', '')}")
            print(f"     - Avg. Cost: {row.get('Avg. Cost', '')}")
            break
    
    if not listing_found:
        print(f"   [FAIL] Item 11127 NOT FOUND in ItemListingReport")

# Check ItemMovementReport
print("\n2. Checking ItemMovementReport.csv...")
items_with_transactions = []
current_item_code = ""
item_11127_transactions = []

with open(SOURCE_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    next(reader)  # Skip title
    for _ in range(3):  # Skip metadata rows
        try:
            next(reader)
        except StopIteration:
            break
    
    for row in reader:
        if not row or not row[0].strip():
            continue
        
        first = row[0].strip()
        
        if first.lower().startswith("total for item:"):
            current_item_code = ""
            continue
        
        # Check if it's an item header
        if " - " in first and not first[0].isdigit():
            parts = first.split(" - ", 1)
            current_item_code = parts[0].strip()
        elif current_item_code and len(row) >= 5:
            # It's a transaction row
            desc = row[2].strip()
            is_purchase = desc == "Supplier Invoice"
            is_sale = desc == "Tax Invoice"
            
            if current_item_code == "11127":
                item_11127_transactions.append({
                    "date": first,
                    "desc": desc,
                    "qty": row[4].strip(),
                    "is_purchase": is_purchase,
                    "is_sale": is_sale
                })
            
            # Count items with actual purchases/sales
            if is_purchase or is_sale:
                items_with_transactions.append(current_item_code)

print(f"\n   Item 11127 transactions found: {len(item_11127_transactions)}")
for i, txn in enumerate(item_11127_transactions, 1):
    print(f"   Transaction {i}:")
    print(f"     - Date: {txn['date']}")
    print(f"     - Description: {txn['desc']}")
    print(f"     - Quantity: {txn['qty']}")
    print(f"     - Is Purchase: {txn['is_purchase']}")
    print(f"     - Is Sale: {txn['is_sale']}")

unique_items = set(items_with_transactions)
print(f"\n   Total unique items with purchases/sales: {len(unique_items)}")
print(f"   Item 11127 has purchase/sale transactions: {'11127' in unique_items}")

# Explain the issue
print("\n" + "=" * 70)
print("ROOT CAUSE ANALYSIS:")
print("=" * 70)
print("""
The aggregation logic in item_movement_by_cat.py (lines 311-318) only includes
items that have at least ONE purchase (Supplier Invoice) OR sale (Tax Invoice)
transaction.

Item 11127 has:
  - 1 transaction: "Adjustment" on 05/10/2023
  - is_purchase = False (not "Supplier Invoice")
  - is_sale = False (not "Tax Invoice")

Result: Item 11127 is filtered out during aggregation because it has no
purchases or sales, only an adjustment.

This is INTENTIONAL behavior - the report focuses on items with actual
movement (purchases/sales), not just inventory adjustments.
""")

print("=" * 70)
print("SOLUTION OPTIONS:")
print("=" * 70)
print("""
Option 1: Include ALL items from ItemListingReport (even without transactions)
  - Modify aggregate_items() to iterate over item_listing_map instead of agg
  - Items without transactions would show 0 for purchased/sold

Option 2: Keep current behavior (recommended)
  - Report shows only items with actual movement
  - Adjustments don't indicate active inventory management
  - Keeps report focused and actionable

Option 3: Add a separate "Inactive Items" tab
  - Show items from ItemListingReport with no transactions
  - Useful for identifying obsolete stock
""")
