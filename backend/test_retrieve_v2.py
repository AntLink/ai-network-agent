import struct
import sys
sys.path.insert(0, r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend")
from csms_client import CSMSClient, HDR

c = CSMSClient("192.168.162.20", timeout=30)
c.connect()
r = c.greeting()
print("token:", c.token.hex())

# Try retrieve with taskId=10 as measureId
req_body = c.token + struct.pack("<I", 10)
c.marker += 1
c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + req_body)
resp = c.recv()
print("retrieve taskId=10:", resp)
if resp:
    print(f"  measureId={int.from_bytes(resp.body[:4],'little')} status={int.from_bytes(resp.body[-8:-4],'little')}")

# Also try with measureId=5595
req_body2 = c.token + struct.pack("<I", 5595)
c.marker += 1
c.sock.sendall(HDR.pack(c.marker, 0, 27, 1, 2, 71002, 4) + req_body2)
resp2 = c.recv()
print("retrieve 5595:", resp2)
if resp2:
    b = resp2.body
    print(f"  measureId={int.from_bytes(b[:4],'little')} status={int.from_bytes(b[-8:-4],'little')}")

c.close()