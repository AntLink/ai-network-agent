import struct
import sys
import time
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
if not resp or resp.msg_type == 9999:
    print("schedule failed")
    c.close()
    exit()

# Parse schedule ID from response (offset 24)
sched_id = int.from_bytes(resp.body[24:28], 'little')
print(f"Scheduled taskId: {sched_id}")

# Now poll retrieve with incrementing measureIds
print("\nPolling for measurement result...")
for mid in range(5595, 5620):
    c.marker += 1
    body = c.token + struct.pack("<I", mid)
    c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + struct.pack("<I", mid))
    resp = c.recv()
    if resp and resp.msg_type != 9999:
        print(f"measureId={mid}: type={resp.msg_type} sub={resp.subtype} status={int.from_bytes(resp.body[-8:-4],'little')} bodyLen={resp.body_len}")
        if resp.msg_type == 27 and resp.subtype == 72002:
            print("SUCCESS! Got measurement data")
            break
    else:
        status = int.from_bytes(resp.body[-8:-4], 'little') if resp and resp.body_len >= 8 else -1
        print(f"  mid={mid}: type={resp.msg_type if resp else 'none'} status={status}")
    time.sleep(0.1)

c.close()