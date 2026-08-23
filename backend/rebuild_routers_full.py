"""Rebuild penuh R1+R2 di IDE: dialog->base config->OSPF->bukti tersimpan."""
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


class Console:
    def __init__(self, port, timeout_boot=300):
        self.s = socket.create_connection((VM, port), timeout=10)
        self.s.settimeout(0.5)
        self.buf = ""
        t0 = time.time()
        while time.time() - t0 < timeout_boot:
            self.s.send(b"\r")
            c = clean(recv_all(self.s, 2))
            lines = [l.strip() for l in c.splitlines() if l.strip()]
            if lines and PROMPT_RE.search(lines[-1]):
                break
            time.sleep(3)

    def read_until(self, timeout=60):
        self.buf = ""
        t0 = time.time()
        while time.time() - t0 < timeout:
            c = clean(recv_all(self.s, 1.0))
            self.buf += c
            lines = [l.strip() for l in self.buf.splitlines()
                     if l.strip()]
            ll = lines[-1] if lines else ""
            if PROMPT_RE.search(ll):
                return "prompt", ll
            if ll.endswith(":"):
                return "ask", ll
        return "timeout", ""

    def send(self, c):
        for ch in c:
            self.s.send(ch.encode())
            time.sleep(0.03)
        self.s.send(b"\r")

    def cmd(self, c, timeout=90, answers=None):
        answers = answers or {}
        self.send(c)
        kind, ll = self.read_until(timeout)
        n = 0
        while kind == "ask" and n < 6:
            resp = ""
            for key, val in answers.items():
                if key.lower() in ll.lower():
                    resp = val
                    break
            print(f"     ? {ll[:40]} -> {repr(resp)[:25]}")
            self.send(resp)
            kind, ll = self.read_until(timeout)
            n += 1
        err = [l for l in self.buf.splitlines()
               if l.strip().startswith(("Invalid", "Incomplete",
                                        "% Invalid"))]
        tag = "X" if err else " "
        print(f" [{tag}] {c}")
        return self.buf

    def ensure_ready(self):
        """Bersihkan wizard awal; pastikan prompt # tercapai."""
        for _ in range(15):
            self.send("")
            kind, ll = self.read_until(8)
            joined = self.buf
            if "[yes/no]" in joined:
                self.send("no")
                continue
            if kind == "prompt" and ll.endswith("#"):
                return True
            if kind == "prompt" and ll.endswith(">"):
                self.cmd("enable", 10)
                continue
            if "Would you like" in joined or "yes/no" in joined:
                self.send("no")
        return False


BASE_CFG = {
    "R1": [
        "hostname R1", "enable secret Admin123!",
        "username admin privilege 15 secret Admin123!",
        "ip domain-name lab.local", "ip ssh version 2",
        "line vty 0 4", "login local", "transport input ssh", "exit",
        "interface GigabitEthernet0/0",
        "description MGMT-OOB",
        "ip address 172.22.45.249 255.255.240.0", "no shutdown", "exit",
        "interface GigabitEthernet0/1",
        "description TRUNK-LAN-A", "no shutdown", "exit",
        "interface GigabitEthernet0/1.10",
        "encapsulation dot1Q 10",
        "ip address 192.168.10.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/1.20",
        "encapsulation dot1Q 20",
        "ip address 192.168.20.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/2",
        "description WAN-TO-MK1",
        "ip address 10.255.10.2 255.255.255.252", "no shutdown", "exit",
        "interface GigabitEthernet0/3",
        "description BACKUP-TO-R2",
        "ip address 10.255.12.1 255.255.255.252", "no shutdown", "exit",
    ],
    "R2": [
        "hostname R2", "enable secret Admin123!",
        "username admin privilege 15 secret Admin123!",
        "ip domain-name lab.local", "ip ssh version 2",
        "line vty 0 4", "login local", "transport input ssh", "exit",
        "interface GigabitEthernet0/0",
        "description MGMT-OOB",
        "ip address 172.22.36.184 255.255.240.0", "no shutdown", "exit",
        "interface GigabitEthernet0/1",
        "description TRUNK-LAN-B", "no shutdown", "exit",
        "interface GigabitEthernet0/1.10",
        "encapsulation dot1Q 10",
        "ip address 192.168.30.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/1.20",
        "encapsulation dot1Q 20",
        "ip address 192.168.40.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/2",
        "description WAN-TO-MK1",
        "ip address 10.255.20.2 255.255.255.252", "no shutdown", "exit",
        "interface GigabitEthernet0/3",
        "description BACKUP-TO-R1",
        "ip address 10.255.12.2 255.255.255.252", "no shutdown", "exit",
    ],
}

OSPF = {
    "R1": dict(rid="1.1.1.1", nets=[
        ("10.255.10.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
        ("192.168.10.0", "0.0.0.255"), ("192.168.20.0", "0.0.0.255")]),
    "R2": dict(rid="2.2.2.2", nets=[
        ("10.255.20.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
        ("192.168.30.0", "0.0.0.255"), ("192.168.40.0", "0.0.0.255")]),
}

for name, port in [("R1", 5006), ("R2", 5008)]:
    print("=" * 24, name, "=" * 24)
    c = Console(port)
    if not c.ensure_ready():
        print(" [X] konsol belum siap!")
        continue
    c.cmd("terminal length 0")

    o = c.cmd("dir flash:", 45)
    flash_ok = not ("%Error" in o or "No such device" in o)
    print("   [FLASH]", "OK" if flash_ok else "MASIH RUSAK - STOP!")

    c.cmd("configure terminal")
    for cmd_ in BASE_CFG[name]:
        c.cmd(cmd_)
    c.cmd("crypto key generate rsa modulus 1024", 60,
          answers={"confirm": "\r", "bits": "1024"})
    c.cmd("router ospf 1")
    c.cmd("router-id " + OSPF[name]["rid"])
    for net, mask in OSPF[name]["nets"]:
        c.cmd(f"network {net} {mask} area 0")
    c.cmd("passive-interface GigabitEthernet0/1.10")
    c.cmd("passive-interface GigabitEthernet0/1.20")
    c.cmd("end")
    c.cmd("write memory", 180)

    print("--- BUKTI TERSIMPAN ---")
    o = c.cmd("show startup-config | include hostname|router ospf",
              60)
    saved = [l.strip() for l in o.splitlines()
             if ("hostname" in l or "ospf" in l.lower())
             and not l.strip().startswith("show")]
    ok = any(f"hostname {name}" in s_ for s_ in saved) and \
        any("router ospf" in s_ for s_ in saved)
    for s_ in saved[:4]:
        print("   ", s_[:70])
    print("   [PERSISTEN]", "TERBUKTI!" if ok else "GAGAL!!!")
    c.s.close()

print("")
print("[i] menunggu adjacency OSPF 60s...")
time.sleep(60)

import paramiko
try:
    cc = paramiko.SSHClient()
    cc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cc.connect("172.22.37.168", username="admin", password="admin",
               timeout=15, allow_agent=False, look_for_keys=False)
    i, o, e = cc.exec_command("/routing ospf neighbor print", timeout=30)
    out = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "",
                 o.read().decode(errors="replace"))
    nf = out.count('"Full"')
    print(f"[MK-1] neighbor Full: {nf}")
    for l in out.splitlines():
        if 'state="Full"' in l:
            print("   ", l.strip()[:80])
    cc.close()
except Exception as ex:
    print("[MK-1] ERROR:", ex)

print("")
print("=== SELESAI ===")