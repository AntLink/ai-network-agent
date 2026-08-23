"""Scan semua konsol node GNS3 di 172.22.40.30."""
import socket
import time
from concurrent.futures import ThreadPoolExecutor

HOST = "172.22.40.30"
RANGE = range(5000, 5151)


def grab(port):
    try:
        s = socket.create_connection((HOST, port), timeout=1.2)
    except Exception:
        return None
    s.settimeout(0.8)
    banner = b""
    try:
        time.sleep(0.3)
        s.send(b"\r\n")
        start = time.time()
        while time.time() - start < 1.5:
            try:
                d = s.recv(300)
                if not d:
                    break
                banner += d
                start = time.time()
            except socket.timeout:
                break
    except Exception:
        pass
    finally:
        s.close()
    return banner.decode(errors="replace").strip() if banner else None


with ThreadPoolExecutor(max_workers=40) as ex:
    results = dict(zip(RANGE, ex.map(grab, RANGE)))

print(f"Port aktif dengan banner di {HOST}:")
for port, b in sorted(results.items()):
    if b:
        # ambil beberapa baris terakhir yang bersih
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        tail = " | ".join(lines[-3:])[:150]
        print(f"  {port}: {tail}")