#!/usr/bin/env python3
import sys
sys.path.insert(0, r'C:\Users\mohfa\PycharmProjects\ai-network-agent\csms_live')
from csms_client import CSMSClient
import struct

c = CSMSClient('192.168.162.20', timeout=30)
c.connect()

resp = c.greeting()
print(f'Greeting: type={resp.msg_type} body={resp.body.hex() if resp and resp.body else None}')

# Schedule measurement
body = c.token + struct.pack('<ddddII', 100e6, 200e6, 1e6, 100e3, 100, 1)
print(f'Schedule body len: {len(body)}')
print(f'Schedule body hex: {body.hex()}')

resp = c.schedule_measurement(body)
if resp:
    print(f'Schedule response: type={resp.msg_type} sub={resp.subtype} bodyLen={resp.body_len}')
    print(f'Schedule response body hex: {resp.body.hex() if resp.body else None}')
    if resp.body and len(resp.body) >= 28:
        task_id = int.from_bytes(resp.body[24:28], 'little')
        print(f'taskId from bytes 24-28: {task_id}')
    
    # Check DB
    import sqlite3
    try:
        db = sqlite3.connect(r'C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsdb.db')
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f'DB tables after schedule: {tables}')
        if tables:
            for table in tables:
                tname = table[0]
                cursor.execute(f'SELECT COUNT(*) FROM {tname}')
                count = cursor.fetchone()[0]
                print(f'{tname}: {count} rows')
                cursor.execute(f'SELECT * FROM {tname} LIMIT 3')
                rows = cursor.fetchall()
                print(f'Sample rows: {rows}')
        db.close()
    except Exception as e:
        print(f'DB error: {e}')

c.close()