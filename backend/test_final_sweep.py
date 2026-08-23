import struct
import sys
import time
import math
sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")
from csms_client import CSMSClient, HDR

c = CSMSClient("192.168.162.20", timeout=30)
c.connect()
r = c.greeting()
print("token:", c.token.hex())

# We know measureId 5590 works, let's get the full sweep data
mid = 5590
c.marker += 1
body = c.token + struct.pack("<I", 5590)
c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + struct.pack("<I", 5590))
resp = c.recv()
if resp and resp.msg_type == 27 and resp.subtype == 72002:
    status = int.from_bytes(resp.body[-8:-4], 'little')
    print(f"retrieve 5590: status={int.from_bytes(resp.body[-8:-4], 'little')} bodyLen={resp.body_len}")
    
    body = resp.body
    mid_val = int.from_bytes(body[:4], 'little')
    print(f"measureId={mid_val}")
    
    # Find sweep data
    import math
    for off in range(4, len(body)-16, 8):
        f = struct.unpack("<d", body[off:off+8])[0]
        pw = struct.unpack("<d", body[off+8:off+16])[0]
        if math.isfinite(f) and math.isfinite(pw) and 1e6 <= f <= 3e9:
            n = 0
            prev = -1e18
            p = off
            pts = []
            while p + 16 <= len(body):
                f2 = struct.unpack("<d", body[p:p+8])[0]
                pw2 = struct.unpack("<d", body[p+8:p+16])[0]
                if not (math.isfinite(f2) and math.isfinite(pw2) and 1e6 <= f2 <= 3e9 and f2 > prev):
                    break
                pts.append((f2, pw2))
                prev = f2
                p += 16
            if len(pts) >= 50:
                print(f"Found sweep at offset {off}: {len(pts)} points")
                print(f"  freq range: {pts[0][0]/1e6:.1f} - {pts[-1][0]/1e6:.1f} MHz")
                print(f"  power range: {min(p for _,p in pts):.1f} - {max(p for _,p in pts):.1f} dBm")
                print(f"  first 10 pts: {[(round(f/1e6,1), round(p,1)) for f,p in pts[:10]]}")
                print(f"  last 10 pts: {[(round(f/1e6,1), round(p,1)) for f,p in pts[-10:]]}")
                # Save raw data
                open(f"sweep_5590.bin", "wb").write(body)
                print("Saved sweep_5590.bin")
                break