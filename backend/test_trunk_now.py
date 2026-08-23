"""Uji trunk dari SW1: SVI ping GW + mac table + counter."""
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


def ios(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    buf, ll = wait_prompt(s, 20)
    if ll.endswith(">"):
        send_cmd(s, "enable")
        b2, _ = wait_prompt(s, 15)
        if "Password" in b2:
            send_cmd(s, "Admin123!")
            wait_prompt(s, 15)
    send_cmd(s, "terminal length 0")
    wait_prompt(s, 8)
    return s


print("========== SW1 -> GW ping ==========")
s = ios(5002)
send_cmd(s, "ping 192.168.10.1 repeat 4")
o, _ = wait_prompt(s, 40)
m = re.search(r"Success rate is \((\d+)/(\d+)\)", o)
print("   SVI->GW:", m.group(0) if m else "?")

send_cmd(s, "show mac address-table dynamic | include Gi0/0|Gi0/1|Gi0/2")
o, _ = wait_prompt(s, 25)
for l in o.splitlines():
    ls = l.strip()
    if re.match(r"\d+\s+[0-9a-f]{4}\.", ls):
        print("   mac:", ls)

send_cmd(s, "show interfaces GigabitEthernet0/0")
o, _ = wait_prompt(s, 20)
mm = re.search(r"(\d+) packets input", o.replace("\n", " "))
mo = re.search(r"(\d+) packets output", o.replace("\n", " "))
print(f"   Gi0/0: in={mm.group(1) if mm else '?'} "
      f"out={mo.group(1) if mo else '?'}")
send_cmd(s, "show interfaces GigabitEthernet0/1")
o, _ = wait_prompt(s, 20)
mm = re.search(r"(\d+) packets input", o.replace("\n", " "))
mo = re.search(r"(\d+) packets output", o.replace("\n", " "))
print(f"   Gi0/1: in={mm.group(1) if mm else '?'} "
      f"out={mo.group(1) if mo else '?'}")
s.close()

print("")
print("========== R1 Gi0/1 counters ==========")
s = ios(5006)
send_cmd(s, "show interfaces GigabitEthernet0/1")
o, _ = wait_prompt(s, 20)
mi = re.search(r"(\d+) packets input", o.replace("\n", " "))
mo = re.search(r"(\d+) packets output", o.replace("\n", " "))
print(f"   Gi0/1: in={mi.group(1) if mi else '?'} "
      f"out={mo.group(1) if mo else '?'}")

send_cmd(s, "ping 192.168.10.10 repeat 3")
o, _ = wait_prompt(s, 35)
m = re.search(r"Success rate is \((\d+)/(\d+)\)", o)
print("   R1->PC-A1:", m.group(0) if m else "?")

send_cmd(s, "show ip arp | include 192.168")
o, _ = wait_prompt(s, 20)
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith(("Internet", "Protocol")):
        print("   ", ls[:80])
s.close()