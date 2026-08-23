"""Debug mentah konsol SW2 - dump semua traffic."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=3.0):
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
    return buf


def show(buf, title):
    txt = buf.decode(errors="replace")
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "{ESC}", txt)
    print(f"--- {title} ---")
    for l in txt.splitlines():
        if l.strip():
            print("   |", repr(l.rstrip())[:130])


s = socket.create_connection((VM, 5004), timeout=10)
s.settimeout(0.5)

show(recv_all(s, 4), "banner awal")
s.send(b"\r")
show(recv_all(s, 3), "setelah ENTER")

print("\n>>> kirim: enable")
for ch in "enable":
    s.send(ch.encode())
    time.sleep(0.05)
s.send(b"\r")
show(recv_all(s, 6), "respons enable")

print("\n>>> kirim: Admin123!")
for ch in "Admin123!":
    s.send(ch.encode())
    time.sleep(0.05)
s.send(b"\r")
show(recv_all(s, 8), "respons password")

print("\n>>> kirim: show version (tes priv)")
for ch in "show version | include System image":
    s.send(ch.encode())
    time.sleep(0.03)
s.send(b"\r")
show(recv_all(s, 10), "hasil")

s.close()