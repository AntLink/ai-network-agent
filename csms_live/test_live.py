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

# Schedule a measurement
body = c.token
body += struct.pack("<ddddII",
    100e6,   # start freq Hz
    200e6,   # stop freq Hz
    1e6,     # step Hz
    100e3,   # RBW Hz
    100,     # dwell ms
    1        # sweep type
)
c.marker += 1
pkt = HDR.pack(c.marker, 0, 27, 5, 2, 71000, len(body)) + body
c.sock.sendall(pkt)
resp = c.recv()
print("schedule:", resp)
sched_id = int.from_bytes(resp.body[24:28], 'little')
print(f"Scheduled taskId: {sched_id}")

print("\nWaiting for measurement to complete...")
time.sleep(3)

print("\nPolling for measurement result...")
for mid in range(5590, 5620):
    c.marker += 1
    body = c.token + struct.pack("<I", mid)
    c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + struct.pack("<I", mid))
    resp = c.recv()
    if resp and resp.msg_type == 27 and resp.subtype == 72002:
        status = int.from_bytes(resp.body[-8:-4], 'little')
        print(f"mid={mid}: status={status} bodyLen={resp.body_len}")
        if resp.body_len > 10000:
            print(f"  SUCCESS! measureId={mid}, bodyLen={resp.body_len}")
            body = resp.body
            mid_val = int.from_bytes(body[:4], 'little')
            print(f"  measureId={mid_val}")
            for off in range(4, len(resp.body)-16, 8):
                f = struct.unpack("<d", resp.body[off:off+8])[0]
                pw = struct.unpack("<d", resp.body[off+8:off+16])[0]
                if math.isfinite(f) and math.isfinite(pw) and 1e6 <= f <= 3e9:
                    n = 0
                    prev = -1e18
                    p = off
                    pts = []
                    while p + 16 <= len(resp.body):
                        f2 = struct.unpack("<d", resp.body[p:p+8])[0]
                        pw2 = struct.unpack("<d", resp.body[p+8:p+16])[0]
                        if not (math.isfinite(f2) and math.isfinite(pw2) and 1e6 <= f2 <= 3e9 and f2 > prev):
                            break
                        pts.append((f2, pw2))
                        prev = f2
                        p += 16
                    if len(pts) >= 50:
                        print(f"  Found sweep at offset {off}: {len(pts)} points")
                        print(f"  freq range: {pts[0][0]/1e6:.1f} - {pts[-1][0]/1e6:.1f} MHz")
                        print(f"  power range: {min(p for _,p in pts):.1f} - {max(p for _,p in pts):.1f} dBm")
                        print(f"  first 10 pts: {[(round(f/1e6,1), round(p,1)) for f,p in pts[:10]]}")
                        open(f"sweep_{mid}.bin", "wb").write(resp.body)
                        print(f"Saved sweep_{mid}.bin")
                        break
            break
    else:
        status = int.from_bytes(resp.body[-8:-4], 'little') if resp and resp.body_len >= 8 else -1
        if resp.body_len > 100:
            print(f"  mid={mid}: status={status} bodyLen={resp.body_len}")
    time.sleep(0.1)

c.close()