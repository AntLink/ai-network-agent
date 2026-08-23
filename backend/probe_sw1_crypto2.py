"""Coba generate RSA keys via config mode / crypto pki di SW1."""
import socket
import time
import re

HOST, PORT = "172.22.40.30", 5003


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


def slow_send(s, cmd, wait=3):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    out = recv_all(s, wait)
    print(f">> {cmd}")
    print(clean(out))
    return out


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1)

slow_send(s, "enable", 1.5)

# opsi crypto pki
slow_send(s, "crypto pki ?", 2)

# coba di config mode
slow_send(s, "configure terminal", 2)
out = slow_send(s, "crypto key generate rsa modulus 2048", 8)
if "[yes/no]" in out or "confirm" in out.lower() or "How many bits" in out or "[512]" in out:
    s.send(b"\r")
    print(clean(recv_all(s, 8)))
slow_send(s, "end", 2)

print("\n=== VERIFIKASI ===")
slow_send(s, "show crypto key mypubkey rsa", 3)
slow_send(s, "show ip ssh | include SSH", 3)

s.close()