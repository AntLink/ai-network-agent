"""Verifikasi cepat SW1/SW2 pasca konfigurasi."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().-]+[#>]\s*$")


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


def wait_prompt(s, timeout=60):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        chunk = clean(recv_all(s, 1.5))
        if chunk:
            buf += chunk
            lines = [l.strip() for l in buf.splitlines() if l.strip()]
            if lines and PROMPT_RE.search(lines[-1]):
                return buf, lines[-1]
        else:
            s.send(b"\r")
    return buf, ""


def cmd(s, c, timeout=90):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")
    out, _ = wait_prompt(s, timeout)
    return out


for name, port in [("SW1", 5002), ("SW2", 5004)]:
    print("=" * 22, name, "=" * 22)
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    s.send(b"\r")
    out, prompt = wait_prompt(s, 30)
    print("   prompt:", prompt)
    if ">" in prompt.splitlines()[-1]:
        s.send(b"enable\r")
        o, _ = wait_prompt(s, 15)
        if "Password" in o:
            s.send(b"Admin123!\r")
            wait_prompt(s, 15)
    cmd(s, "terminal length 0")

    o = cmd(s, "dir flash:", 45)
    flash_ok = not ("No such device" in o or "%Error" in o)
    files = len([l for l in o.splitlines()
                 if re.match(r"\s*\d+\s+-", l)])
    print(f"   flash: {'OK' if flash_ok else 'RUSAK'} ({files} file)")

    o = cmd(s, "show vlan brief", 90)
    ok10 = bool(re.search(r"^10\s+\S+", "\n".join(o.splitlines()), re.M))
    ok20 = bool(re.search(r"^20\s+\S+", "\n".join(o.splitlines()), re.M))
    print(f"   vlan10={ok10} vlan20={ok20}")

    o = cmd(s, "show interfaces trunk", 60)
    print("   trunk Gi0/0:", "OK" if "Gi0/0" in o else "TIDAK ADA")

    o = cmd(s, "show ip interface brief | include Vlan", 45)
    for l in o.splitlines():
        if "Vlan" in l:
            print("   ", l.strip())

    o = cmd(s, "show running-config | include hostname|access vlan|trunk",
            60)
    for l in o.splitlines():
        ls = l.strip()
        if ls.startswith(("hostname", "switchport")):
            print("   ", ls)

    o = cmd(s, "show startup-config | include hostname", 60)
    saved = [l.strip() for l in o.splitlines()
             if "hostname" in l and not l.strip().startswith("show")]
    print("   startup tersimpan:", saved[0] if saved else "KOSONG!")
    s.close()

print("")
print("=== PING END-TO-END ANTAR PC ===")


def vpcs_ping(port, target, label):
    try:
        s = socket.create_connection((VM, port), timeout=10)
        s.settimeout(0.5)
        recv_all(s, 2)
        s.send(b"\r")
        recv_all(s, 1)
        for ch in f"ping {target}":
            s.send(ch.encode())
            time.sleep(0.02)
        s.send(b"\r")
        out = recv_all(s, 18)
        replies = len(re.findall(r"icmp_seq=\d+ ttl=", out))
        status = ("SUKSES" if replies >= 3 else
                  ("sebagian" if replies else "GAGAL"))
        print(f"   {label:<26} -> {target:<16} {replies}/4 [{status}]")
        s.close()
        return replies >= 3
    except Exception as e:
        print(f"   {label}: ERROR {e}")
        return False


vpcs_ping(5010, "192.168.10.1", "PC-A1 -> GW-A")
vpcs_ping(5014, "192.168.30.1", "PC-B1 -> GW-B")
vpcs_ping(5018, "192.168.100.1", "PC-M -> GW-M")
vpcs_ping(5010, "192.168.30.10", "PC-A1 -> PC-B1 (lintas situs)")
vpcs_ping(5010, "192.168.100.10", "PC-A1 -> PC-M (ke LAN-M)")
vpcs_ping(5016, "192.168.20.10", "PC-B2 -> PC-A2 (VLAN20)")
print("")
print("=== SELESAI ===")