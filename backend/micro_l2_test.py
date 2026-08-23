"""Uji L2 mikro: bersihkan mac-table, PC-A1 ping, cek mac-table lagi."""
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


# SW1 session
s = socket.create_connection((VM, 5002), timeout=10)
s.settimeout(0.5)
recv_all(s, 3)
send_cmd(s, "")
wait_prompt(s, 30)
o, _ = wait_prompt(s, 3)
last = o.strip().splitlines()[-1] if o.strip() else ""
if not last.endswith("#"):
    send_cmd(s, "enable")
    o, _ = wait_prompt(s, 15)
    if "Password" in o:
        send_cmd(s, "Admin123!")
        wait_prompt(s, 15)
send_cmd(s, "terminal length 0")
wait_prompt(s, 8)

send_cmd(s, "clear mac address-table dynamic")
wait_prompt(s, 8)

# PC-A1 ping GW (fire and forget)
p = socket.create_connection((VM, 5010), timeout=10)
p.settimeout(0.5)
recv_all(p, 2)
send_cmd(p, "")
recv_all(p, 1)
send_cmd(p, "ping 192.168.10.1")
print("[i] PC-A1 ping dikirim, menunggu 20s...")
time.sleep(20)
out_pc = clean(recv_all(p, 5))
print("--- output PC ---")
print(out_pc[-600:])
p.close()

send_cmd(s, "show mac address-table dynamic")
o = clean(recv_all(s, 12))
print("--- mac table setelah traffic ---")
for l in o.splitlines():
    ls = l.rstrip()
    if re.match(r"\s*\d+\s+[0-9a-f]{4}\.", ls):
        print("   ", ls.strip())
if not re.search(r"[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}", o):
    print("   (KOSONG - tidak ada MAC yang dipelajari!)")
s.close()