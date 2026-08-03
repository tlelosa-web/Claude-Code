#!/usr/bin/env python3
"""
Script to find tender opportunities for groceries/food supplies in Gauteng, South Africa.

Uses the tenders-sa tool to search for relevant tenders.
"""

import subprocess
import sys
import os
import sqlite3

def get_goods_tenders_gauteng():
    """Get all goods tenders in Gauteng from cache."""
    db_path = os.path.join(os.path.dirname(__file__), "..", "cache.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT title, description, department, close_date, value_amount, contacts.name, contacts.email FROM tenders LEFT JOIN contacts ON tenders.ocid = contacts.tender_ocid WHERE category = ? AND province = ?", ('goods', 'Gauteng'))
    rows = c.fetchall()
    conn.close()
    return rows

def filter_food_related(tenders):
    """Filter tenders that might be related to food/groceries."""
    keywords = ['food', 'catering', 'supplies', 'consumables', 'groceries', 'provision', 'meal']
    filtered = []
    for row in tenders:
        text = (row[0] + ' ' + row[1]).lower()  # title + description
        if any(kw in text for kw in keywords):
            filtered.append(row)
    return filtered

if __name__ == "__main__":
    tenders = get_goods_tenders_gauteng()
    food_tenders = filter_food_related(tenders)
    
    report_path = os.path.join(os.path.dirname(__file__), "..", "3_Live_Reports", "gauteng_food_tenders.txt")
    with open(report_path, "w") as f:
        f.write("Tender Opportunities for Groceries/Food Supplies in Gauteng\n")
        f.write("=" * 60 + "\n\n")
        
        if food_tenders:
            for title, desc, dept, close, value, name, email in food_tenders:
                f.write(f"Title: {title}\n")
                f.write(f"Description: {desc}\n")
                f.write(f"Department: {dept}\n")
                f.write(f"Close Date: {close}\n")
                f.write(f"Value: R{value:,.0f}\n" if value else "Value: N/A\n")
                f.write(f"Contact: {name} <{email}>\n" if name else "Contact: N/A\n")
                f.write("-" * 40 + "\n\n")
        else:
            f.write("No food-related tenders found in current cache.\n")
            f.write("Consider fetching more data or checking different keywords.\n")
    
    print(f"Report generated: {report_path}")
    if food_tenders:
        print(f"Found {len(food_tenders)} potential opportunities.")
    else:
        print("No opportunities found.")