"""Cek L2 SW1: CDP neighbor, trunk, vlan, mac-table + R1 ping PC."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=4.0):
    buf = b""
    start = time.time()
    while time.time() - start < wait:
        try:
            d = s.recv(65535)
            if not d:
                break
            buf += d
            start = time.time()
        except socket.timeout:
            break
    return buf.decode(errors="replace")


def clean(txt):
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt


def slow(s, cmd, wait=10):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    return clean(recv_all(s, wait))


print("========== SW1 ==========")
s = socket.create_connection((VM, 5002), timeout=10)
s.settimeout(1)
recv_all(s, 3)
slow(s, "", 2)
slow(s, "enable", 5)
slow(s, "terminal length 0", 5)
for cmd in ["show cdp neighbors",
            "show interfaces trunk",
            "show vlan brief",
            "show mac address-table dynamic"]:
    out = slow(s, cmd, 14)
    print(">>", cmd)
    keep = [l.rstrip() for l in out.splitlines()
            if l.strip() and not l.strip().startswith(("show", "SW1"))][:18]
    print("\n".join(keep))
    print("-" * 55)
s.close()

print("")
print("========== R1 -> PC pings ==========")
s = socket.create_connection((VM, 5006), timeout=10)
s.settimeout(1)
recv_all(s, 3)
slow(s, "", 2)
slow(s, "enable", 5)
slow(s, "terminal length 0", 5)
for tgt in ["192.168.10.10", "192.168.20.10"]:
    o = slow(s, f"ping {tgt} repeat 3", 20)
    m = re.search(r"Success rate is \((\d+)/(\d+)\)", o)
    print(f"   R1 -> {tgt}: {m.group(0) if m else 'tanpa hasil'}")
o = slow(s, "show ip arp | include 192.168", 8)
for l in o.splitlines():
    if "192.168." in l:
        print("   ARP:", l.rstrip())
s.close()