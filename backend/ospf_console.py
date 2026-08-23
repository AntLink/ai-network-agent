"""OSPF R1 & R2 via konsol (slow-send) - jalur paling andal."""
import re
import socket
import time

VM = "172.22.37.68"

TARGETS = {
    "R1": dict(port=5006, rid="1.1.1.1",
               nets=[("10.255.10.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
                     ("192.168.10.0", "0.0.0.255"),
                     ("192.168.20.0", "0.0.0.255")]),
    "R2": dict(port=5008, rid="2.2.2.2",
               nets=[("10.255.20.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
                     ("192.168.30.0", "0.0.0.255"),
                     ("192.168.40.0", "0.0.0.255")]),
}


def recv_all(s, wait=3.0):
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
    txt = re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt


def slow(s, cmd, wait=5):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    out = clean(recv_all(s, wait))
    bad = ("Invalid" in out) or ("Incomplete" in out)
    print(" [" + ("X" if bad else " ") + "] " + cmd)
    return out


for name, cfg in TARGETS.items():
    print("==========", name, "==========")
    s = socket.create_connection((VM, cfg["port"]), timeout=10)
    s.settimeout(1)
    recv_all(s, 3)
    slow(s, "", 2)
    slow(s, "enable", 4)
    slow(s, "terminal length 0", 4)
    slow(s, "configure terminal", 5)
    slow(s, "router ospf 1", 5)
    slow(s, "router-id " + cfg["rid"], 4)
    for n, m in cfg["nets"]:
        slow(s, f"network {n} {m} area 0")
    slow(s, "passive-interface GigabitEthernet0/1.10")
    slow(s, "passive-interface GigabitEthernet0/1.20")
    slow(s, "end", 4)
    o = slow(s, "write memory", 12)
    print(" [*] simpan:", "OK" if "OK" in o else "PERIKSA")
    s.close()

print("")
print("menunggu adjacency 45s...")
time.sleep(45)

print("=== neighbor & route via SSH legacy ===")
from legacy_ssh import connect_legacy, shell_send

for ip, label in [("172.22.45.249", "R1"), ("172.22.36.184", "R2")]:
    print("--- " + label + " ---")
    try:
        c = connect_legacy(ip)
        sh = c.invoke_shell() if hasattr(c, "invoke_shell") else c
        time.sleep(3)
        while sh.recv_ready():
            sh.recv(65535)
        shell_send(sh, "terminal length 0", 2)
        o = shell_send(sh, "show ip ospf neighbor", 10)
        for l in o.splitlines():
            if "FULL" in l:
                print("   " + l.rstrip())
        o = shell_send(sh, "show ip route ospf | include ^O", 8)
        for l in o.splitlines():
            if l.strip().startswith("O"):
                print("   " + l.rstrip())
    except Exception as e:
        print("   gagal:", type(e).__name__, str(e)[:80])