#!/usr/bin/env python3
"""
Test scheduling a measurement and checking if DB gets populated.
"""

import sys
sys.path.insert(0, r'C:\Users\mohfa\PycharmProjects\ai-network-agent\csms_live')
from csms_client import CSMSClient
import struct
import time

def main():
    c = CSMSClient("192.168.162.20", timeout=30)
    c.connect()
    
    # Step 1: Greeting
    resp = c.greeting()
    if not resp or resp.msg_type != 0x2176:
        print("❌ Greeting failed")
        return
    
    print(f"[+] Connected! Token: {c.token.hex()}")
    
    # Step 2: Schedule a measurement
    body = c.token + struct.pack("<ddddII", 
        100e6,   # 100 MHz start
        200e6,   # 200 MHz stop
        1e6,     # 1 MHz step
        100e3,   # 100 kHz RBW
        100,     # 100 ms dwell
        1        # sweep type
    )
    
    resp = c.schedule_measurement(body)
    if not resp:
        print("❌ Schedule failed")
        return
    
    print(f"[+] Schedule response: type={resp.msg_type} sub={resp.subtype} bodyLen={resp.body_len}")
    task_id = int.from_bytes(resp.body[24:28], 'little') if resp.body_len >= 28 else 0
    print(f"[+] taskId: {task_id}")
    
    # Wait a moment
    time.sleep(1)
    
    # Check DB
    import sqlite3
    try:
        db = sqlite3.connect(r'C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\csmsdb.db')
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"[+] DB tables: {tables}")
        
        if tables:
            for table in tables:
                tname = table[0]
                cursor.execute(f'SELECT COUNT(*) FROM {tname}')
                count = cursor.fetchone()[0]
                print(f"[+] {tname}: {count} rows")
                cursor.execute(f'SELECT * FROM {tname} LIMIT 3')
                rows = cursor.fetchall()
                print(f"[+] Sample rows: {rows}")
        db.close()
    except Exception as e:
        print(f"[!] DB error: {e}")
    
    # Step 3: Try retrieve measurement with various measureIds
    print("\n[+] Trying retrieve measurement...")
    for mid in range(5590, 5600):
        resp = c.retrieve_measurement(measure_id=mid)
        if resp and resp.msg_type == 0x1B and resp.subtype == 0x1C22:
            print(f"[+] SUCCESS! measureId={mid}, bodyLen={resp.body_len}")
            # Print first 32 bytes hex
            print(f"[+] Body hex: {resp.body[:32].hex()}")
            break
        time.sleep(0.1)
    
    c.close()

if __name__ == "__main__":
    main()