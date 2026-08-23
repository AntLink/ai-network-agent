#!/usr/bin/env python3
"""
CSMS Live Frequency Monitoring - Quick Start Example

Usage:
    python example_usage.py

Requirements:
- Python 3.x
- Network access to CSMS device (default: 192.168.162.20:3302)
"""

import sys
import struct
import time
import math
sys.path.insert(0, ".")
from csms_client import CSMSClient, HDR

def main():
    # Connect to CSMS device
    c = CSMSClient("192.168.162.20", timeout=30)
    c.connect()
    
    # Step 1: Greeting (mandatory first step)
    resp = c.greeting()
    if not resp or resp.msg_type != 0x2176:  # 8566 = GREETING_RES
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
        print("[!] Schedule failed")
        return
    task_id = int.from_bytes(resp.body[24:28], 'little') if resp.body_len >= 28 else 0
    print(f"[+] Scheduled taskId: {task_id}")
    print(f"[DEBUG] Schedule response: type={resp.msg_type} sub={resp.subtype} bodyLen={resp.body_len} body={resp.body.hex()}")
    
    # Wait for measurement to complete
    import time
    time.sleep(3)
    
    # Step 3: Poll for measurement result
    for mid in range(5590, 5620):
        resp = c.retrieve_measurement(measure_id=mid)
        if resp and resp.msg_type == 0x1B and resp.subtype == 0x1C22:  # 72002
            if resp.body_len > 10000:
                print(f"[+] SUCCESS! measureId={mid}, bodyLen={resp.body_len}")
                body = resp.body
                import math
                for off in range(4, len(body)-16, 8):
                    f = struct.unpack("<d", body[off:off+8])[0]
                    pw = struct.unpack("<d", body[off+8:off+16])[0]
                    if math.isfinite(f) and math.isfinite(f) and 1e6 <= f <= 3e9:
                        n = 0; prev = -1e18; p = off; pts = []
                        while p + 16 <= len(body):
                            f2 = struct.unpack("<d", body[p:p+8])[0]
                            pw2 = struct.unpack("<d", body[p+8:p+16])[0]
                            if not (math.isfinite(f2) and math.isfinite(f2) and 1e6 <= f2 <= 3e9 and f2 > prev):
                                break
                            pts.append((f2, pw2))
                            prev = f2; p += 16
                        if len(pts) >= 50:
                            print(f"  Sweep: {len(pts)} points, {pts[0][0]/1e6:.1f}-{pts[-1][0]/1e6:.1f} MHz")
                            print(f"  Power: {min(p for _,p in pts):.1f}-{max(p for _,p in pts):.1f} dBm")
                            break
                break
        time.sleep(0.1)
    else:
        print("[-] No valid measurement found")

if __name__ == "__main__":
    main()