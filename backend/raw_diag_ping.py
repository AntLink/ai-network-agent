"""Dump mentah ping R1->PC dan kondisi PC-A1."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().>-]+[#>]\s*$")


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
        c = clean(recv_all(s, 1.0))
        buf += c
        ll = buf.strip().splitlines()[-1].strip() if buf.strip() else ""
        if PROMPT_RE.search(ll):
            return buf, ll
        if ll.endswith(":") and "More" not in ll:
            s.send(b"\r")
    return buf, ""


def send_cmd(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")


# ---------- R1 ping RAW ----------
print("========== R1 -> PC-A1 (raw) ==========")
s = socket.create_connection((VM, 5006), timeout=10)
s.settimeout(0.5)
recv_all(s, 3)
send_cmd(s, "")
wait_prompt(s, 30)
o, _ = wait_prompt(s, 5)
if not o.rstrip().endswith("#"):
    send_cmd(s, "enable")
    o, _ = wait_prompt(s, 15)
    if "Password" in o:
        send_cmd(s, "Admin123!")
        wait_prompt(s, 15)
send_cmd(s, "terminal length 0")
wait_prompt(s, 10)

send_cmd(s, "ping 192.168.10.10 repeat 4 timeout 2")
buf = ""
t0 = time.time()
while time.time() - t0 < 45:
    c = clean(recv_all(s, 1.5))
    buf += c
    ll = buf.strip().splitlines()[-1] if buf.strip() else ""
    if PROMPT_RE.search(ll.strip()):
        break
print(buf[-1400:])
s.close()

# ---------- PC-A1 raw ----------
print("")
print("========== PC-A1 raw ==========")
s = socket.create_connection((VM, 5010), timeout=10)
s.settimeout(0.5)
recv_all(s, 3)
send_cmd(s, "")
recv_all(s, 2)

print("--- show ip ---")
send_cmd(s, "show ip")
print(clean(recv_all(s, 6))[:500])

print("--- arp ---")
send_cmd(s, "arp")
print(clean(recv_all(s, 6))[:400])

print("--- ping GW ---")
send_cmd(s, "ping 192.168.10.1")
out = clean(recv_all(s, 20))
print(out[-700:])
s.close()