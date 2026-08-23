"""Diagnosa mgmt path dari sisi R1 via konsol."""
import socket
import time
import re

VM = "172.22.37.68"
PORT = 5006  # R1


def recv_all(s, wait=2.0):
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
    out = clean(recv_all(s, wait))
    print(f">> {cmd}")
    print(out[:900])
    return out


s = socket.create_connection((VM, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1.5)

slow(s, "enable", 1.5)
slow(s, "terminal length 0")
slow(s, "show ip interface brief | exclude unassigned")
slow(s, "show interfaces GigabitEthernet0/0 | include line protocol|Internet address", 3)
slow(s, "ping 172.22.32.1", 6)
slow(s, "show cdp neighbors", 4)
s.close()