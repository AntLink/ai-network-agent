"""Setup ulang IP semua PC + verifikasi OSPF + ping end-to-end."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().>-]+[#>]\s*$")


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


def pc_setup(port, name, ip, gw):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    recv_all(s, 1.5)
    send_cmd(s, f"ip {ip} {gw} 24")
    recv_all(s, 3)
    send_cmd(s, "save")
    recv_all(s, 3)
    send_cmd(s, "show ip")
    o = clean(recv_all(s, 5))
    m = re.search(r"IP/MASK\s*:\s*([0-9.]+/\d+)", o)
    got = m.group(1) if m else "?"
    print(f"   {name:<7}: {got} gw {gw} [{'OK' if got.startswith(ip.rsplit('.',1)[0]) else 'CEK!'}]")
    s.close()


print("[1] Setup IP semua PC")
pcs = [
    (5010, "PC-A1", "192.168.10.10", "192.168.10.1"),
    (5012, "PC-A2", "192.168.20.10", "192.168.20.1"),
    (5014, "PC-B1", "192.168.30.10", "192.168.30.1"),
    (5016, "PC-B2", "192.168.40.10", "192.168.40.1"),
    (5018, "PC-M", "192.168.100.10", "192.168.100.1"),
]
for port, name, ip, gw in pcs:
    try:
        pc_setup(port, name, ip, gw)
    except Exception as e:
        print(f"   {name}: ERROR {e}")


def ios_session(port):
    """Konsol IOS: tunggu prompt, enable bila perlu."""
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    for attempt in range(20):
        send_cmd(s, "")
        buf = clean(recv_all(s, 4))
        lines = [l.strip() for l in buf.splitlines() if l.strip()]
        ll = lines[-1] if lines else ""
        if ll.endswith("#"):
            return s
        if ll.endswith(">"):
            send_cmd(s, "enable")
            b2 = clean(recv_all(s, 5))
            if "Password" in b2:
                send_cmd(s, "Admin123!")
                recv_all(s, 5)
            continue
        # masih booting - tunggu
        time.sleep(10)
    return s


print("")
print("[2] Verifikasi OSPF di ketiga router (tunggu konvergensi)...")
for name, port in [("R1", 5006), ("R2", 5008)]:
    try:
        s = ios_session(port)
        send_cmd(s, "terminal length 0")
        recv_all(s, 3)
        send_cmd(s, "show ip ospf neighbor")
        o = ""
        t0 = time.time()
        while time.time() - t0 < 25:
            o += clean(recv_all(s, 1))
            if re.search(r"#\s*$", o.strip(), re.M):
                break
        fulls = [l.strip()[:60] for l in o.splitlines() if "FULL" in l]
        print(f"   {name}: {len(fulls)} FULL")
        for f_ in fulls:
            print("      ", f_)
        s.close()
    except Exception as e:
        print(f"   {name}: ERROR {e}")

try:
    import paramiko
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect("172.22.37.168", username="admin", password="admin",
              timeout=15, allow_agent=False, look_for_keys=False)

    def ros(cmd, t=30):
        i, o, e = c.exec_command(cmd, timeout=t)
        return re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "",
                      o.read().decode(errors="replace"))

    out = ros("/routing ospf neighbor print")
    nfull = out.count('"Full"')
    print(f"   MK-1  : {nfull} Full")
    c.close()
except Exception as e:
    print(f"   MK-1: ERROR {e}")

print("")
print("[3] PING END-TO-END")
TESTS = [
    (5010, "192.168.10.1", "A1->GW"),
    (5014, "192.168.30.1", "B1->GW"),
    (5018, "192.168.100.1", "M->GW"),
    (5010, "192.168.30.10", "A1->B1"),
    (5010, "192.168.100.10", "A1->M"),
    (5016, "192.168.20.10", "B2->A2"),
]
for port, tgt, label in TESTS:
    try:
        s = socket.create_connection((VM, port), timeout=10)
        s.settimeout(0.5)
        recv_all(s, 2)
        send_cmd(s, "")
        recv_all(s, 1.5)
        send_cmd(s, f"ping {tgt}")
        out = clean(recv_all(s, 26))
        replies = len(re.findall(r"bytes from", out))
        stat = "SUKSES" if replies >= 4 else ("sebagian" if replies else "GAGAL")
        print(f"   {label:<10} -> {tgt:<16} {replies}/5 [{stat}]")
        if replies == 0:
            tail = [l.strip() for l in out.splitlines() if l.strip()]
            if tail:
                print("        ", tail[-1][:80])
        s.close()
    except Exception as e:
        print(f"   {label}: ERROR {e}")

print("")
print("=== SELESAI ===")