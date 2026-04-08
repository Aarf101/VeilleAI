import sqlite3
import os

db_path = 'watcher.db'
if os.path.exists(db_path):
    print(f"Database {db_path} exists. Size: {os.path.getsize(db_path)} bytes")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        for table in tables:
            t_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {t_name}")
            count = cursor.fetchone()[0]
            print(f"Table '{t_name}' has {count} rows.")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {t_name} LIMIT 1")
                columns = [description[0] for description in cursor.description]
                row = cursor.fetchone()
                print(f"Sample row from '{t_name}':")
                print(dict(zip(columns, row)))
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Database {db_path} does not exist.")
