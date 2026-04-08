import sqlite3
import os

db_path = 'watcher.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Insert a dummy item
try:
    cursor.execute("""
    INSERT INTO items (url, title, published, summary, source, fetched_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ('https://example.com/test', 'Test Article', '2026-04-02T12:00:00Z', 'Summary', 'Example', '2026-04-02T12:00:00Z 00:00:00'))
    conn.commit()
    print("Inserted dummy article.")
except Exception as e:
    print(f"Error: {e}")

conn.close()
