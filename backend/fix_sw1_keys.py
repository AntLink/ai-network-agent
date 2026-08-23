"""Perbaiki SSH keys di SW1 via konsol."""
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


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1)

s.send(b"enable\r\n")
recv_all(s, 1.5)

print("=== STATUS KEYS SAAT INI ===")
s.send(b"show crypto key mypubkey rsa\r\n")
print(clean(recv_all(s, 3)))

print("\n=== GENERATE ULANG (full output) ===")
s.send(b"crypto key generate rsa modulus 2048\r\n")
time.sleep(4)
out = recv_all(s, 8)
print(clean(out))

# jika diminta konfirmasi overwrite
if "[yes/no]" in out or "[confirm]" in out or "Do you really" in out:
    s.send(b"yes\r\n")
    print(clean(recv_all(s, 8)))

print("\n=== VERIFIKASI ===")
s.send(b"show crypto key mypubkey rsa\r\n")
print(clean(recv_all(s, 3)))
s.send(b"show ip ssh | include SSH|version\r\n")
print(clean(recv_all(s, 3)))

s.send(b"write memory\r\n")
out = recv_all(s, 5)
print("\nWRITE MEMORY:", "OK" if "OK" in out or "Building" in out else repr(clean(out)[-200:]))

s.close()