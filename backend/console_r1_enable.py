"""Konsol R1 via telnet GNS3 (172.22.40.30:5005) - coba enable."""
import socket
import time

HOST, PORT = "172.22.40.30", 5005


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


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)
print("=== AWAL ===")
print(repr(recv_all(s, 2)))

def send(cmd, wait=2):
    s.send(cmd.encode() + b"\r\n")
    out = recv_all(s, wait)
    print(f"\n>> {cmd}")
    print(repr(out))
    return out

send("show privilege")
send("enable", 3)

client.close if False else None
s.close()