import sqlite3

db_path = r'C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsdb.db'
db = sqlite3.connect(db_path)
cursor = db.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

for table in tables:
    tname = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {tname}')
    count = cursor.fetchone()[0]
    print(f'{tname}: {count} rows')
    
    cursor.execute(f'SELECT * FROM {tname} LIMIT 3')
    rows = cursor.fetchall()
    print(f'Sample rows: {rows}')

db.close()