import struct
import sys
sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")
from csms_client import CSMSClient, HDR

c = CSMSClient("192.168.162.20", timeout=15)
c.connect()
r = c.greeting()
print("token:", c.token.hex())

# Try retrieve with measureId=5596 (next after 5595)
c.marker += 1
req_body = c.token + struct.pack("<I", 5596)
c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + struct.pack("<I", 5596))
resp = c.recv()
if resp:
    b = resp.body
    print(f"retrieve 5596: measureId={int.from_bytes(b[:4],'little')} status={int.from_bytes(b[-8:-4],'little')} bodyLen={resp.body_len}")
else:
    print("retrieve 5596: no response")

c.close()