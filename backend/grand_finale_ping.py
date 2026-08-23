"""UJI PAMUNGKAS: ping end-to-end semua PC."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=1.5):
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


def vpcs_ping(port, target):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 2)
    send_cmd(s, "")
    recv_all(s, 1)
    send_cmd(s, f"ping {target}")
    out = ""
    t0 = time.time()
    while time.time() - t0 < 32:
        out += clean(recv_all(s, 1.0))
        if out.count("\n") >= 4 and ("bytes from" in out or
                                     "not reachable" in out or
                                     "100.00%" in out):
            if len(re.findall(r"bytes from", out)) >= 5 or \
                    "not reachable" in out or "100.00%" in out:
                break
    replies = len(re.findall(r"bytes from", out))
    s.close()
    return replies, out


TESTS = [
    (5010, "192.168.10.1", "PC-A1 -> GW-A"),
    (5012, "192.168.20.1", "PC-A2 -> GW-A"),
    (5014, "192.168.30.1", "PC-B1 -> GW-B"),
    (5016, "192.168.40.1", "PC-B2 -> GW-B"),
    (5018, "192.168.100.1", "PC-M  -> GW-M"),
    (5010, "192.168.30.10", "PC-A1 -> PC-B1  [lintas situs]"),
    (5010, "192.168.100.10", "PC-A1 -> PC-M   [ke LAN-M]"),
    (5016, "192.168.20.10", "PC-B2 -> PC-A2  [VLAN20 lintas]"),
]

print("=" * 55)
print("   UJI KONEKTIVITAS END-TO-END")
print("=" * 55)
total_ok = 0
for port, tgt, label in TESTS:
    try:
        n, raw = vpcs_ping(port, tgt)
        ok = n >= 4
        total_ok += ok
        stat = "SUKSES" if ok else ("sebagian" if n else "GAGAL")
        print(f"  {label:<28} {n}/5  [{stat}]")
        if n == 0:
            tail = [l.strip() for l in raw.splitlines() if l.strip()]
            print("      ", tail[-1][:70] if tail else "(kosong)")
    except Exception as e:
        print(f"  {label:<28} ERROR {e}")

print("=" * 55)
print(f"   HASIL: {total_ok}/{len(TESTS)} tes lulus")
print("=" * 55)