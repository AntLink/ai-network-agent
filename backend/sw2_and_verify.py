"""Setup SW2 (pabrikan) + verifikasi final SW1 & SW2."""
import socket
import time
import re

VM = "172.22.37.68"
ESC = chr(27)

SW2_CMDS = [
    "hostname SW2",
    "enable secret Admin123!",
    "username admin privilege 15 secret Admin123!",
    "ip domain-name lab.local",
    "crypto key generate rsa modulus 2048",
    "ip ssh version 2",
    "line vty 0 4", "login local", "privilege level 15",
    "transport input ssh", "exit",
    "vlan 10", "name USERS-B", "exit",
    "vlan 20", "name SERVERS-B", "exit",
    "interface GigabitEthernet0/0",
    "description TRUNK-TO-R2",
    "switchport trunk encapsulation dot1q",
    "switchport mode trunk", "exit",
    "interface GigabitEthernet0/1",
    "description PC-B1",
    "switchport mode access",
    "switchport access vlan 10", "exit",
    "interface GigabitEthernet0/2",
    "description PC-B2",
    "switchport mode access",
    "switchport access vlan 20", "exit",
    "interface Vlan1",
    "ip address 172.22.39.10 255.255.240.0",
    "no shutdown", "exit",
    "ip default-gateway 172.22.32.1",
]


def recv_all(s, wait=6.0):
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


def slow(s, cmd, wait=8):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.04)
    s.send(b"\r")
    out = clean(recv_all(s, wait))
    bad = ("Invalid" in out) or ("Incomplete" in out)
    print(" [" + ("X" if bad else " ") + "] " + cmd)
    return out


def connect(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    recv_all(s, 10)
    t0 = time.time()
    while time.time() - t0 < 150:
        s.send(b"\r")
        out = clean(recv_all(s, 5))
        if "[yes/no]" in out:
            s.send(b"no\r")
            continue
        if re.search(r"Switch[>#]", out):
            print(" [ ] prompt siap (" + str(int(time.time() - t0)) + "s)")
            return s
    s.close()
    return None


# ---------- SETUP SW2 ----------
print("========== SETUP SW2 (:5004) ==========")
s = connect(5004)
if s:
    slow(s, "enable", 8)
    slow(s, "terminal length 0", 8)
    slow(s, "configure terminal", 8)
    for cmd in SW2_CMDS:
        wait = 30 if cmd.startswith("crypto") else 8
        out = slow(s, cmd, wait=wait)
        if cmd.startswith("crypto") and ("confirm" in out.lower() or "[yes/no]" in out):
            s.send(b"\r")
            recv_all(s, 25)
    slow(s, "end", 8)
    out = slow(s, "write memory", 40)
    print(" [*] write memory -> " + ("OK" if "OK" in out or "Building" in out else "PERIKSA"))
    s.close()

# ---------- VERIFIKASI KEDUA SWITCH ----------
for name, port, ip in [("SW1", 5002, "172.22.38.10"), ("SW2", 5004, "172.22.39.10")]:
    print("")
    print("========== VERIFIKASI " + name + " ==========")
    s = connect(port)
    if not s:
        continue
    slow(s, "enable", 8)
    slow(s, "terminal length 0", 8)
    v = slow(s, "show ip interface brief", 20)
    for l in v.splitlines():
        if "Vlan1" in l or "GigabitEthernet0/0" in l or "GigabitEthernet0/1" in l \
           or "GigabitEthernet0/2" in l:
            print("   " + l.rstrip())
    sv = slow(s, "show startup-config | include hostname", 25)
    hl = [l.strip() for l in sv.splitlines() if "hostname" in l]
    print(" [ ] startup: " + (hl[-1] if hl else "?"))
    p = slow(s, "ping 172.22.32.1", 30)
    rate = re.search(r"Success rate is \((\d+)/(\d+)\)", p)
    print(" [ ] ping gw -> " + (rate.group(0) if rate else "tanpa hasil"))
    s.close()

print("")
print("=== SELESAI ===")