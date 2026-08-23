"""Dump mentah: R1 config/OSPF + PC-A1 setup."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().>-]+[#>]\s*$")


def recv_all(s, wait=2.5):
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
        time.sleep(0.03)
    s.send(b"\r")


def wait_prompt(s, timeout=45):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = clean(recv_all(s, 1.0))
        buf += c
        lines = [l.strip() for l in buf.splitlines() if l.strip()]
        ll = lines[-1] if lines else ""
        if PROMPT_RE.search(ll):
            return buf, ll
    return buf, ""


print("========== R1 ==========")
s = socket.create_connection((VM, 5006), timeout=10)
s.settimeout(0.5)
recv_all(s, 4)
send_cmd(s, "")
buf, ll = wait_prompt(s, 60)
print("   prompt:", ll[:40])
if ll.endswith(">"):
    send_cmd(s, "enable")
    buf, _ = wait_prompt(s, 20)
    if "Password" in buf:
        send_cmd(s, "Admin123!")
        wait_prompt(s, 20)
send_cmd(s, "terminal length 0")
wait_prompt(s, 10)

for cmd_ in [
    "show running-config | include hostname|router ospf|network|ip address",
    "show ip ospf neighbor",
    "show ip route | include ^O|^C",
    "show ip arp",
]:
    print(f"--- {cmd_} ---")
    send_cmd(s, cmd_)
    o, _ = wait_prompt(s, 40)
    for l in o.splitlines():
        ls = l.strip()
        if ls and not ls.startswith(("show", "R1")) \
                and not ls.startswith("Building"):
            print("   ", ls[:110])
s.close()

print("")
print("========== PC-A1 ==========")
p = socket.create_connection((VM, 5010), timeout=10)
p.settimeout(0.5)
recv_all(p, 4)
send_cmd(p, "")
recv_all(p, 2)
send_cmd(p, "show ip")
o = clean(recv_all(p, 6))
print(o[:450])
send_cmd(p, "ip 192.168.10.10 192.168.10.1 24")
o = clean(recv_all(p, 6))
print("setelah set ip:")
print(o[:300])
send_cmd(p, "show ip")
o = clean(recv_all(p, 6))
m = re.search(r"IP/MASK\s*:\s*(\S+)", o)
print("IP sekarang:", m.group(1) if m else "?")
p.close()