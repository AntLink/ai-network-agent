"""Finalisasi SW2: SVI + default-gateway + crypto + write memory."""
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


def cmd(s, c, timeout=120):
    send_raw(s, c)
    out, _ = wait_prompt(s, timeout)
    bad = any(k in out for k in ("Invalid", "Incomplete", "% "))
    print(" [" + ("X" if bad else " ") + "] " + c)
    return out


s = socket.create_connection((VM, 5004), timeout=10)
s.settimeout(0.5)
recv_all(s, 3)
send_raw(s, "")
wait_prompt(s, 30)
send_raw(s, "enable")
out, _ = wait_prompt(s, 15)
if "Password" in out or ">" in out.splitlines()[-1]:
    send_raw(s, "Admin123!")
    wait_prompt(s, 15)
cmd(s, "terminal length 0")

cmd(s, "configure terminal")
cmd(s, "hostname SW2")
cmd(s, "enable secret Admin123!")
cmd(s, "username admin privilege 15 secret Admin123!")
cmd(s, "ip domain-name lab.local")
cmd(s, "ip ssh version 2")
cmd(s, "ip ssh time-out 60")
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
    if "Vlan" in l:
        print("   ", l.strip())
s.close()
print("")
print("=== SW2 SELESAI ===")