import struct
import sys
sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")
from csms_client import CSMSClient, HDR

c = CSMSClient("192.168.162.20", timeout=30)
c.connect()
r = c.greeting()
print("token:", c.token.hex())

# First, schedule a measurement
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
print("sched:", resp)
if resp and resp.body_len >= 28:
    # parse schedule ID from response
    sched_id = int.from_bytes(resp.body[24:28], 'little')
    print(f"Schedule ID: {sched_id}")
    
    # Now retrieve measurement
    c.marker += 1
    body2 = c.token + struct.pack("<I", sched_id)  # retrieve by schedule ID
    c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + body2)
    resp2 = c.recv()
    print("retrieve:", resp2)
    if resp2 and resp2.body_len > 4:
        print("  measureId:", int.from_bytes(resp2.body[:4], 'little'))
        print("  status:", int.from_bytes(resp2.body[-8:-4], 'little'))
        print("  bodyLen:", resp2.body_len)
        # save body
        open(r"C:\Users\mohfa\AppData\Local\Temp\opencode\meas_sched.bin", "wb").write(resp2.body)
        print("  saved to meas_sched.bin")
else:
    print("schedule failed")

c.close()