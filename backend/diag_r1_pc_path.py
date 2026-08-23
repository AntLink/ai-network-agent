"""Diagnosis lintas-lapis: R1 <-> SW1 <-> PC-A1."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().-]+[#>]\s*$")


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


def last_line(txt):
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    return lines[-1] if lines else ""


class Console:
    def __init__(self, port):
        self.s = socket.create_connection((VM, port), timeout=10)
        self.s.settimeout(0.5)
        self.buf = ""

    def read_until(self, timeout=90, allow_enter=True):
        self.buf = ""
        t0 = time.time()
        while time.time() - t0 < timeout:
            c = clean(recv_all(self.s, 1.0))
            self.buf += c
            ll = last_line(self.buf)
            if PROMPT_RE.search(ll):
                return "prompt", ll
            if ll.endswith(":"):
                return "ask", ll
            if not self.buf and allow_enter and time.time() - t0 > 4:
                self.s.send(b"\r")
        return "timeout", last_line(self.buf)

    def send(self, c):
        for ch in c:
            self.s.send(ch.encode())
            time.sleep(0.02)
        self.s.send(b"\r")

    def cmd(self, c, timeout=120, answers=None):
        answers = answers or {}
        self.send(c)
        kind, ll = self.read_until(timeout)
        for _ in range(4):
            if kind == "ask":
                resp = ""
                for key, val in answers.items():
                    if key.lower() in ll.lower():
                        resp = val
                        break
                self.send(resp)
                kind, ll = self.read_until(timeout)
                continue
            break
        return self.buf


# ---------- R1 ----------
print("========== R1 ==========")
c = Console(5006)
c.s.send(b"\r")
kind, ll = c.read_until(30, allow_enter=False)
if not ll.endswith("#"):
    c.send("enable")
    kind, ll = c.read_until(15)
    if kind == "ask":
        c.send("Admin123!")
        c.read_until(15)
c.cmd("terminal length 0")
o = c.cmd("show ip interface brief | include Gig", 45)
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith("Gigabit"):
        print("   ", ls)
for tgt in ["192.168.10.10", "192.168.20.10"]:
    o = c.cmd(f"ping {tgt} repeat 3", 40)
    m = re.search(r"Success rate is \((\d+)/(\d+)\)", o)
    print(f"   R1 -> {tgt}: {m.group(0) if m else 'tanpa hasil'}")
o = c.cmd("show ip arp | include 192.168", 30)
print("   --- ARP ---")
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith(("Internet", "Protocol")) and "incomplete" not in ls:
        print("   ", ls[:100])
c.s.close()

# ---------- SW1 mac table ----------
print("")
print("========== SW1 mac-table ==========")
c = Console(5002)
c.s.send(b"\r")
kind, ll = c.read_until(30, allow_enter=False)
if not ll.endswith("#"):
    c.send("enable")
    kind, ll = c.read_until(15)
    if kind == "ask":
        c.send("Admin123!")
        c.read_until(15)
c.cmd("terminal length 0")
o = c.cmd("show mac address-table dynamic", 60)
for l in o.splitlines():
    ls = l.rstrip()
    if re.match(r"\s*\d+\s+[0-9a-f]{4}\.", ls):
        print("   ", ls.strip())
o = c.cmd("show interfaces status", 60)
for l in o.splitlines():
    ls = l.rstrip()
    if ls.startswith(("Port", "Gi")):
        print("   ", ls)
c.s.close()

# ---------- PC-A1 ----------
print("")
print("========== PC-A1 ==========")
c = Console(5010)
c.s.send(b"\r")
recv_all(c.s, 1)
o = c.cmd("ip", 20)
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith(("ip ", "name")):
        print("   ", ls[:80])
o = c.cmd("show ip", 20)
m = re.search(r"ip:\d+\.\d+\.\d+\.\d+.*", o)
if m:
    print("   ", m.group(0)[:90])
c.cmd("arp", 15)
c.close() if hasattr(c, "close") else c.s.close()