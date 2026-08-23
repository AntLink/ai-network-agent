"""Finalisasi SW2 v2 - dengan enable yang dijamin masuk mode #."""
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


def wait_prompt(s, timeout=90):
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


def send_raw(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")


def ensure_priv(s):
    """Pastikan berada di prompt '#' (privileged)."""
    send_raw(s, "")
    _, p = wait_prompt(s, 30)
    for _ in range(4):
        cur = p.splitlines()[-1] if p else ""
        print("   [prompt]", cur[:40])
        if cur.endswith("#"):
            return True
        send_raw(s, "enable")
        out, p = wait_prompt(s, 20)
        joined = out + p
        if "Password" in joined:
            send_raw(s, "Admin123!")
            out2, p = wait_prompt(s, 20)
            if "Bad secrets" in out2:
                print("   !! password enable ditolak")
                return False
    return False


def cmd(s, c, timeout=120):
    send_raw(s, c)
    out, p = wait_prompt(s, timeout)
    err = [l.strip() for l in out.splitlines()
           if l.strip().startswith(("Invalid", "Incomplete"))]
    print(" [" + ("X" if err else " ") + "] " + c)
    for e in err[:1]:
        print("     !!", e[:110])
    return out


s = socket.create_connection((VM, 5004), timeout=10)
s.settimeout(0.5)
recv_all(s, 3)

if not ensure_priv(s):
    raise SystemExit("GAGAL masuk mode privileged")

cmd(s, "terminal length 0")

# cek dulu apakah config sebelumnya sudah sebagian masuk
o = cmd(s, "show running-config | include hostname|^ username", 60)
print("--- run saat ini ---")
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith(("hostname", "username")):
        print("   ", ls)

cmd(s, "configure terminal")
cmd(s, "hostname SW2")
cmd(s, "enable secret Admin123!")
cmd(s, "username admin privilege 15 secret Admin123!")
cmd(s, "ip domain-name lab.local")
cmd(s, "ip ssh version 2")
cmd(s, "line vty 0 4")
cmd(s, "login local")
cmd(s, "transport input ssh")
cmd(s, "exit")
cmd(s, "interface Vlan10")
cmd(s, "ip address 192.168.30.2 255.255.255.0")
cmd(s, "no shutdown")
cmd(s, "exit")
cmd(s, "ip default-gateway 192.168.30.1")
cmd(s, "end")

o = cmd(s, "crypto key generate rsa", 60)
if "[confirm]" in o or "bits" in o.lower():
    send_raw(s, "1024")
    wait_prompt(s, 60)

cmd(s, "write memory", 240)

print("--- verifikasi akhir ---")
o = cmd(s, "show startup-config | include hostname", 60)
saved = [l.strip() for l in o.splitlines()
         if "hostname" in l and not l.strip().startswith("show")]
print("   startup:", saved[0] if saved else "KOSONG!")
o = cmd(s, "show ip interface brief | include Vlan", 45)
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith("Vlan"):
        print("   ", ls)
s.close()
print("")
print("=== SW2 SELESAI ===")