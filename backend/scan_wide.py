"""Scan cepat port terbuka + identifikasi banner (rentang luas)."""
import socket
import time
from concurrent.futures import ThreadPoolExecutor

HOST = "172.22.40.30"
START, END = 5000, 6050


def tcp_open(port):
    try:
        s = socket.create_connection((HOST, port), timeout=0.8)
        s.close()
        return port
    except Exception:
        return None


def banner(port):
    try:
        s = socket.create_connection((HOST, port), timeout=2)
        s.settimeout(0.8)
        time.sleep(0.3)
        s.send(b"\r\n")
        data = b""
        start = time.time()
        while time.time() - start < 2:
            try:
                d = s.recv(300)
                if not d:
                    break
                data += d
                start = time.time()
            except socket.timeout:
                break
        s.close()
        return data.decode(errors="replace").strip()
    except Exception:
        return ""


with ThreadPoolExecutor(max_workers=100) as ex:
    results = list(ex.map(tcp_open, range(START, END)))

open_ports = [p for p in results if p]
print(f"Port terbuka: {open_ports}\n")

for p in open_ports:
    b = banner(p)
    lines = [l.strip() for l in b.splitlines() if l.strip()]
    tail = " | ".join(lines[-2:])[:120] if lines else "(diam)"
    print(f"  {p}: {tail}")