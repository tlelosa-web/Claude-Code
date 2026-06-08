"""
Add related_wo_id column to works_order table for combined orders
"""
import sqlite3
import sys
from pathlib import Path

# Get database path
db_path = Path(__file__).parent.parent / 'instance' / 'sops.db'

if not db_path.exists():
    print(f"Database not found at {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(works_order)")
columns = [col[1] for col in cursor.fetchall()]

if 'related_wo_id' in columns:
    print("Column 'related_wo_id' already exists")
else:
    # Add the column
    cursor.execute("ALTER TABLE works_order ADD COLUMN related_wo_id INTEGER REFERENCES works_order(id)")
    conn.commit()
    print("Added 'related_wo_id' column to works_order table")

conn.close()
print("Migration complete")
