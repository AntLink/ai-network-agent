"""Cek isi running-config bagian vlan/switchport di SW1."""
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


def slow(s, cmd, wait=8):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    return clean(recv_all(s, wait))


s = socket.create_connection((VM, 5002), timeout=10)
s.settimeout(1)
recv_all(s, 3)
slow(s, "", 2)
o = slow(s, "enable", 4)
if "Password" in o:
    slow(s, "Admin123!", 5)
slow(s, "terminal length 0", 5)

out = slow(s, "show running-config | include vlan|access", 25)
print("=== run | include vlan|access ===")
for l in out.splitlines():
    ls = l.strip()
    if ls and not ls.startswith(("show", "SW1")) and "Building" not in ls:
        print("   ", l.rstrip())

out = slow(s, "show vlan brief", 25)
print("=== vlan brief penuh ===")
for l in out.splitlines():
    if l.strip() and not l.strip().startswith(("show", "SW1")):
        print("   ", l.rstrip())
s.close()