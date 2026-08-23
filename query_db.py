import sqlite3

db_paths = [
    r'C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csms_bridge\csmsdb_live.db',
    r'C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsdb.db'
]

for db_path in db_paths:
    print(f"\n=== {db_path} ===")
    try:
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print('Tables:', tables)
        
        for table in tables:
            tname = table[0]
            cursor.execute(f'SELECT * FROM {tname} LIMIT 3')
            rows = cursor.fetchall()
            cursor.execute(f'PRAGMA table_info({tname})')
            cols = cursor.fetchall()
            print(f'\nTable {tname}:')
            print('Columns:', cols)
            print('Sample rows:', rows)
        db.close()
    except Exception as e:
        print(f'Error: {e}')