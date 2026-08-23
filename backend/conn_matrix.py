"""Matriks konektivitas: dari R1 dan dari MK-1."""
import socket
import time
import re

VM = "172.22.37.68"


def recv_all(s, wait=3.0):
    buf = b""
    start = time.time()
    while time.time() - start < wait:
        try:
            d = s.recv(4096)
            if not d:
                break
            buf += d
            start = time.time()
        except socket.timeout:
            break
    return buf.decode(errors="replace")


def clean(txt):
    txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return "\n".join(l.rstrip() for l in txt.splitlines() if l.strip())


def slow(s, cmd, wait=2):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    time.sleep(wait)
    return clean(recv_all(s, wait))


print("========== DARI R1 (konsol :5006) ==========")
s1 = socket.create_connection((VM, 5006), timeout=10)
s1.settimeout(1)
recv_all(s1, 1.5)
slow(s1, "enable", 1.5)
slow(s1, "terminal length 0")
out = slow(s1, "ping 172.22.37.168", wait=14)   # MK ether1 (satu L2)
print(">> ping 172.22.37.168 (MK)")
rate = re.search(r"Success rate is \((\d+)/(\d+)\)", out)
print(f"   -> {rate.group(0) if rate else 'TIDAK ADA HASIL'}")
print(out[-260:])
out = slow(s1, "ping 172.22.37.68", wait=14)    # IP eth0 VM
print(">> ping 172.22.37.68 (VM)")
rate = re.search(r"Success rate is \((\d+)/(\d+)\)", out)
print(f"   -> {rate.group(0) if rate else 'TIDAK ADA HASIL'}")
s1.close()

print("\n========== DARI MK-1 (konsol :5000) ==========")
s2 = socket.create_connection((VM, 5000), timeout=10)
s2.settimeout(1)
recv_all(s2, 2)
slow(s2, "admin"); slow(s2, "admin", 4)
for target in ["172.22.32.1", "10.255.10.2", "172.22.45.249"]:
    out = slow(s2, f"/ping {target} count=3", wait=8)
    ok = len(re.findall(r"seq=\d+ ttl=", out))
    print(f">> /ping {target} -> {ok}/3 balasan")
s2.close()