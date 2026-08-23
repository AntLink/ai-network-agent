"""Diagnosa SW1 & SW2 via konsol: status Vlan1, trunk, ping."""
import socket
import time
import re

VM = "172.22.37.68"
NODES = {"SW1": 5002, "SW2": 5004}


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


def slow(s, cmd, wait=3):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    return clean(recv_all(s, wait))


for name, port in NODES.items():
    print(f"\n========== {name} ({VM}:{port}) ==========")
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    recv_all(s, 2)
    slow(s, "enable", 1.5)
    slow(s, "terminal length 0")
    out = slow(s, "show ip interface brief | include Vlan|GigabitEthernet0/[012] ")
    print(out[:800])
    out = slow(s, "show interfaces trunk", 4)
    print("--- trunk ---")
    print(out[:600])
    out = slow(s, "ping 172.22.32.1", 14)
    rate = re.search(r"Success rate is \((\d+)/(\d+)\)", out)
    print(f">> ping gw -> {rate.group(0) if rate else 'tanpa hasil'}")
    s.close()