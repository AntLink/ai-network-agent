"""Tangkap error mentah 'switchport access vlan' + cek logging."""
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
    s.send(c.encode())
    time.sleep(0.03)
    s.send(b"\r")
    out, p = wait_prompt(s, timeout)
    print(">>", c)
    for l in out.splitlines():
        ls = l.strip()
        if ls and "%" in ls:
            print("   !!", ls[:150])
    return out


s = socket.create_connection((VM, 5002), timeout=10)
s.settimeout(0.5)
recv_all(s, 4)
s.send(b"\r")
wait_prompt(s, 30)
s.send(b"enable\r")
out, _ = wait_prompt(s, 15)
if "Password" in out:
    s.send(b"Admin123!\r")
    wait_prompt(s, 15)
cmd(s, "terminal length 0")

print("=== logging signatur/ATA ===")
o = cmd(s, "show logging | include SIGNATURE|ATA-3", 90)
for l in o.splitlines():
    ls = l.strip()
    if ("SIGNATURE" in ls or "ATA" in ls) and not ls.startswith("show"):
        print("   ", ls[:140])

print("")
print("=== uci vlan 50 ===")
cmd(s, "configure terminal")
cmd(s, "vlan 50")
cmd(s, "exit")
cmd(s, "interface GigabitEthernet0/3")
cmd(s, "switchport mode access")
cmd(s, "switchport access vlan 50")
cmd(s, "end")
o = cmd(s, "show vlan brief", 120)
print("--- hasil ---")
for l in o.splitlines():
    if re.match(r"^\d+\s+\S+", l.strip()) or "VLAN Name" in l:
        print("   ", l.rstrip())
s.close()