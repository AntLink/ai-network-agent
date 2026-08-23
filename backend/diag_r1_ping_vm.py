"""Tes penentu: R1 ping IP GNS3 VM (172.22.37.68) via konsol."""
import socket
import time
import re

VM = "172.22.37.68"
PORT = 5006


def recv_all(s, wait=2.5):
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


def slow(s, cmd, wait=8):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    out = clean(recv_all(s, wait))
    print(f">> {cmd}")
    print(out[-700:])
    return out


s = socket.create_connection((VM, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1.5)
slow(s, "enable", 1.5)
slow(s, "terminal length 0")
slow(s, "ping 172.22.37.68")          # IP eth0 VM
slow(s, "ping 172.22.32.1 repeat 3")  # IP vEthernet Windows
s.close()