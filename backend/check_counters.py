"""Cek counter paket SW1 & R1 - apakah frame benar2 mengalir."""
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


def wait_prompt(s, timeout=60):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = clean(recv_all(s, 1.0))
        buf += c
        ll = buf.strip().splitlines()[-1].strip() if buf.strip() else ""
        if PROMPT_RE.search(ll):
            return buf, ll
    return buf, ""


def send_cmd(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")


def priv_session(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    wait_prompt(s, 30)
    o, _ = wait_prompt(s, 4)
    last = o.strip().splitlines()[-1] if o.strip() else ""
    if not last.endswith("#"):
        send_cmd(s, "enable")
        o, _ = wait_prompt(s, 15)
        if "Password" in o:
            send_cmd(s, "Admin123!")
            wait_prompt(s, 15)
    send_cmd(s, "terminal length 0")
    wait_prompt(s, 10)
    return s


print("========== SW1 counters ==========")
s = priv_session(5002)
send_cmd(s, "show interfaces GigabitEthernet0/0 | include line|packets|output")
o1 = clean(recv_all(s, 8))
time.sleep(12)
send_cmd(s, "")
o2 = clean(recv_all(s, 8))

print("--- t0 ---")
for l in o1.splitlines():
    ls = l.strip()
    if ls.startswith(("Gigabit", "packets input", "packets output")):
        print("   ", ls[:100])
print("--- t+12s ---")
for l in o2.splitlines():
    ls = l.strip()
    if ls.startswith(("packets input", "packets output")):
        print("   ", ls[:100])

print("")
print("--- spanning tree ringkas ---")
send_cmd(s, "show spanning-tree | include ^Gi|ROOT|BLK|FWD|LRN")
o = clean(recv_all(s, 10))
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith("Gi") or "BLK" in ls or "Root" in ls:
        print("   ", ls[:110])
s.close()

print("")
print("========== R1 Gi0/1 counters ==========")
s = priv_session(5006)
send_cmd(s, "show interfaces GigabitEthernet0/1 | include packets")
o = clean(recv_all(s, 8))
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith(("packets input", "packets output")):
        print("   ", ls[:100])
s.close()