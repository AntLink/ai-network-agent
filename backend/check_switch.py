"""Cek mendalam switch Cisco IOSvL2 via konsol 172.22.40.30:5003."""
import socket
import time
import re

HOST, PORT = "172.22.40.30", 5003


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
    seen, out = set(), []
    for l in txt.splitlines():
        l = l.strip()
        if l and l not in seen or l.startswith("%"):
            seen.add(l)
            out.append(l)
        elif l:
            out.append(l)
    return "\n".join(out)


def send(s, cmd, wait=2.5):
    s.send(cmd.encode() + b"\r\n")
    out = recv_all(s, wait)
    print(f"\n>> {cmd}")
    print(clean(out))
    return out


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1)

# masuk privileged
send(s, "enable", 2)

send(s, "show privilege")
send(s, "show ip ssh")
send(s, "show vlan brief", 3)
send(s, "show cdp neighbors", 3)
send(s, "show running-config | include hostname|username|aaa|ip domain|crypto|transport|login local|privilege", 3)
send(s, "show interfaces status", 3)

s.close()
print("\n=== SELESAI ===")