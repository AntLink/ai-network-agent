"""Traceroute aktual antar PC untuk dokumentasi jalur."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=2.0):
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


def send_cmd(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")


def trace(port, target, label):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 2)
    send_cmd(s, "")
    recv_all(s, 1)
    send_cmd(s, f"trace {target}")
    out = ""
    t0 = time.time()
    while time.time() - t0 < 40:
        out += clean(recv_all(s, 1.5))
        lines = [l.strip() for l in out.splitlines()]
        if any("Trace completed" in l or l.startswith(label.split()[0])
               for l in lines[-3:]):
            break
    print(f"--- {label} -> {target} ---")
    for l in out.splitlines():
        ls = l.strip()
        if re.match(r"^\d", ls) or "trace" in ls.lower():
            print("   ", ls[:80])
    s.close()


trace(5010, "192.168.30.10", "PC-A1 -> PC-B1")
print()
trace(5010, "192.168.100.10", "PC-A1 -> PC-M")
print()
trace(5016, "192.168.20.10", "PC-B2 -> PC-A2")