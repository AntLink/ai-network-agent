import struct
import sys
sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")
from csms_client import CSMSClient, HDR

c = CSMSClient("192.168.162.20", timeout=15)
c.connect()
r = c.greeting()
print("token:", c.token.hex())

# Try Pan request (8563) with sub=1, cmdVer=2, respVer=3
body = c.token + struct.pack("<I", 0)  # dummy body
c.marker += 1
pkt = HDR.pack(c.marker, 0, 8563, 2, 3, 1, len(body)) + body
c.sock.sendall(pkt)
resp = c.recv()
print("pan sub1:", resp)

# Try sub2
c.marker += 1
body = c.token + struct.pack("<I", 0)
c.sock.sendall(HDR.pack(c.marker, 0, 8563, 2, 3, 2, len(body)) + body)
resp = c.recv()
print("pan sub2:", resp)

c.close()