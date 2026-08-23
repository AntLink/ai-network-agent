"""Deteksi otomatis IP GNS3 VM + scan identitas semua konsol node."""
import socket
import time
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

MAC_PREFIX = "00-15-5d-38-01"   # prefix NIC GNS3 VM di host ini
PORT_RANGE = range(5000, 5121)


def arp_table():
    out = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
    entries = {}
    for line in out.splitlines():
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F\-]{17})", line)
        if m:
            entries[m.group(1)] = m.group(2).lower()
    return entries


def find_vm_ips():
    """Pastikan ARP fresh: ping sweep subnet lokal /20 lalu baca ARP."""
    print("Ping sweep untuk refresh ARP (bisa ±30s)...")
    ips = [f"172.22.{a}.{b}" for a in range(32, 48) for b in (1, 30, 68, 151)]
    # cukup sampel kecil dulu; kalau tidak ketemu, sweep penuh kolom .1-.10
    def ping(ip):
        subprocess.run(["ping", "-n", "1", "-w", "300", ip],
                       capture_output=True)
        return ip
    with ThreadPoolExecutor(max_workers=40) as ex:
        list(ex.map(ping, ips))

    table = arp_table()
    hits = sorted({ip for ip, mac in table.items()
                   if mac.startswith(MAC_PREFIX.replace(":", "-").lower())})
    return hits


def grab(host, port):
    try:
        s = socket.create_connection((host, port), timeout=1.2)
    except Exception:
        return None
    s.settimeout(0.8)
    try:
        time.sleep(0.3)
        s.send(b"\r\n")
        data = b""
        start = time.time()
        while time.time() - start < 1.8:
            try:
                d = s.recv(400)
                if not d:
                    break
                data += d
                start = time.time()
            except socket.timeout:
                break
    except Exception:
        pass
    finally:
        s.close()
    return data.decode(errors="replace").strip() if data else None


def main():
    ips = find_vm_ips()
    print(f"Kandidat IP GNS3 VM (MAC {MAC_PREFIX}x): {ips}")

    for host in ips:
        if not any(grab(host, p) is not None or True for p in []):
            pass
        with ThreadPoolExecutor(max_workers=60) as ex:
            res = dict(zip(PORT_RANGE, ex.map(lambda p: grab(host, p),
                                              PORT_RANGE)))
        found = {p: b for p, b in res.items() if b}
        print(f"\n===== {host}: {len(found)} konsol =====")
        for p, b in sorted(found.items()):
            lines = [l.strip() for l in b.splitlines() if l.strip()]
            tail = " | ".join(lines[-2:])[:110]
            print(f"  {p}: {tail}")
        if found:
            return host, found
    return None, {}


if __name__ == "__main__":
    host, found = main()
    if not found:
        print("\nTIDAK ADA KONSOL TERDETEKSI - pastikan semua node sudah START")
