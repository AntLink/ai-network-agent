import struct
import sys
sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")
from csms_client import CSMSClient, HDR

c = CSMSClient("192.168.162.20", timeout=30)
c.connect()
r = c.greeting()
print("token:", c.token.hex())

# ScheduleMeasurement: type 27, sub 71000, cmdVer=5, respVer=2
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
if resp:
    print("sched:", resp)
    print("body:", resp.body[:64].hex())
else:
    print("no response")
c.close()