import csv

def test_parse():
    csv_path = r"2_Source_Data\OutstandingPurchaseOrdersBySupplierReport.csv"
    supplier_mapping = {}
    
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        current_supplier = None
        for row in reader:
            if not row or not any(row):
                continue
            
            # Ensure row has enough columns
            while len(row) < 5:
                row.append("")
                
            c0, c1, c2, c3, c4 = row[0], row[1], row[2], row[3], row[4]
            
            # Identify Supplier Row
            if c0 and not c1 and not c2 and "Total" not in c0 and "Page" not in c0 and "Date" not in c0 and "Name" not in c0 and "Fan Move" not in c0 and "Supplier" not in c0:
                current_supplier = c0.strip()
                continue
                
            # Identify Item Line
            if not c0 and not c1 and not c2 and not c3:
                desc = c4.strip()
                if " - " in desc:
                    item_code = desc.split(" - ")[0].strip()
                    if item_code and current_supplier:
                        if item_code not in supplier_mapping:
                            supplier_mapping[item_code] = current_supplier
                                
    print(f"Found {len(supplier_mapping)} unique item codes mapped to suppliers.")
    for k, v in list(supplier_mapping.items())[:10]:
        print(f"{k} -> {v}")

if __name__ == "__main__":
    test_parse()
