"""Finalisasi SW2 v3 - state machine anti-sandung prompt Password."""
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

    def pump(self, wait=1.0):
        c = clean(recv_all(self.s, wait))
        self.buf += c
        return c

    def read_until(self, timeout=90, allow_enter=True):
        """Baca sampai prompt '#/>' atau pertanyaan 'xxx:'.
        Jangan pernah kirim ENTER saat menunggu jawaban."""
        self.buf = ""
        t0 = time.time()
        while time.time() - t0 < timeout:
            self.pump()
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
        """Kirim perintah; jawab pertanyaan dari dict {kata: balasan}."""
        answers = answers or {}
        self.send(c)
        kind, ll = self.read_until(timeout)
        for _ in range(5):
            if kind == "ask":
                resp = None
                for key, val in answers.items():
                    if key.lower() in ll.lower():
                        resp = val
                        break
                if resp is None:
                    resp = ""
                    for key, val in answers.items():
                        if key == "*":
                            resp = val
                print("     ? " + ll[:50], "->", repr(resp)[:30])
                self.send(resp)
                kind, ll = self.read_until(timeout)
                continue
            break
        err = [l.strip() for l in self.buf.splitlines()
               if l.strip().startswith(("Invalid", "Incomplete"))]
        print(" [" + ("X" if err else " ") + "] " + c)
        for e in err[:1]:
            print("     !!", e[:110])
        return self.buf

    def ensure_priv(self):
        self.pump(3)
        self.s.send(b"\r")
        kind, ll = self.read_until(30, allow_enter=False)
        for _ in range(4):
            print("   [prompt]", ll[:40])
            if kind == "prompt" and ll.endswith("#"):
                return True
            self.send("enable")
            kind, ll = self.read_until(20, allow_enter=False)
            if kind == "ask" and "assword" in ll:
                self.send("Admin123!")
                kind, ll = self.read_until(20, allow_enter=False)
                if "Bad secrets" in self.buf:
                    print("   !! password ditolak")
                    return False
        return False


con = Console(5004)
print("[i] connect SW2")
if not con.ensure_priv():
    raise SystemExit("GAGAL privileged")

con.cmd("terminal length 0")
con.cmd("configure terminal")
con.cmd("hostname SW2")
con.cmd("enable secret Admin123!")
con.cmd("username admin privilege 15 secret Admin123!")
con.cmd("ip domain-name lab.local")
con.cmd("ip ssh version 2")
con.cmd("line vty 0 4")
con.cmd("login local")
con.cmd("transport input ssh")
con.cmd("exit")
con.cmd("interface Vlan10")
con.cmd("ip address 192.168.30.2 255.255.255.0")
con.cmd("no shutdown")
con.cmd("exit")
con.cmd("ip default-gateway 192.168.30.1")
con.cmd("end")
con.cmd("crypto key generate rsa", 120,
        answers={"bits": "1024", "confirm": "\r"})
con.cmd("write memory", 240)

print("--- verifikasi akhir ---")
o = con.cmd("show startup-config | include hostname", 60)
saved = [l.strip() for l in o.splitlines()
         if "hostname" in l and not l.strip().startswith("show")]
print("   startup:", saved[0] if saved else "KOSONG!")
o = con.cmd("show ip interface brief | include Vlan", 45)
for l in o.splitlines():
    ls = l.strip()
    if ls.startswith("Vlan"):
        print("   ", ls)
con.s.close()
print("")
print("=== SW2 SELESAI ===")