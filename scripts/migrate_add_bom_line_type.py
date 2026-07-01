"""
Add line_type and parent_line_id columns to bom_line table for nested BOM structure
"""
import sqlite3
import sys
from pathlib import Path

db_path = Path(__file__).parent.parent / 'instance' / 'sops.db'

if not db_path.exists():
    print(f"Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(bom_line)")
columns = [col[1] for col in cursor.fetchall()]

if 'line_type' not in columns:
    cursor.execute("ALTER TABLE bom_line ADD COLUMN line_type VARCHAR(20) DEFAULT 'COMPONENT'")
    print("Added 'line_type' column to bom_line table")

if 'parent_line_id' not in columns:
    cursor.execute("ALTER TABLE bom_line ADD COLUMN parent_line_id INTEGER REFERENCES bom_line(id)")
    print("Added 'parent_line_id' column to bom_line table")

conn.commit()
conn.close()
print("Migration complete")
