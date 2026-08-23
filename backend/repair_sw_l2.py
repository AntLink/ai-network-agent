"""Repair L2 SW1/SW2: enable dgn password, pastikan vlan+access+trunk."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
ENABLE_PW = "Admin123!"


def recv_all(s, wait=4.0):
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
        time.sleep(0.03)
    s.send(b"\r")
    return clean(recv_all(s, wait))


def enable(s):
    """enable + tangani prompt Password bila muncul."""
    out = slow(s, "enable", 4)
    if "Password" in out:
        out = slow(s, ENABLE_PW, 5)
        if "Bad secrets" in out or "Password" in out:
            print(" [X] enable gagal!")
            return False
    print(" [ ] enable OK")
    return True


REPAIR = {
    "SW1": dict(port=5002, cmds=[
        "vlan 10", "name USERS-A", "exit",
        "vlan 20", "name SERVERS-A", "exit",
        "interface GigabitEthernet0/0",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk", "exit",
        "interface GigabitEthernet0/1",
        "switchport mode access",
        "switchport access vlan 10", "exit",
        "interface GigabitEthernet0/2",
        "switchport mode access",
        "switchport access vlan 20", "exit",
    ]),
    "SW2": dict(port=5004, cmds=[
        "vlan 10", "name USERS-B", "exit",
        "vlan 20", "name SERVERS-B", "exit",
        "interface GigabitEthernet0/0",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk", "exit",
        "interface GigabitEthernet0/1",
        "switchport mode access",
        "switchport access vlan 10", "exit",
        "interface GigabitEthernet0/2",
        "switchport mode access",
        "switchport access vlan 20", "exit",
    ]),
}

for name, cfg in REPAIR.items():
    print("==========", name, "==========")
    s = socket.create_connection((VM, cfg["port"]), timeout=10)
    s.settimeout(1)
    recv_all(s, 3)
    slow(s, "", 2)
    if not enable(s):
        s.close()
        continue
    slow(s, "terminal length 0", 4)

    # kondisi awal
    out = slow(s, "show vlan brief", 12)
    has10 = re.search(r"^10\s+\w+", out, re.M)
    print(" [ ] vlan 10 ada:", bool(has10))

    slow(s, "configure terminal", 5)
    for cmd in cfg["cmds"]:
        slow(s, cmd)
    slow(s, "end", 4)
    o = slow(s, "write memory", 12)
    print(" [*] simpan:", "OK" if "OK" in o else "PERIKSA")

    # verifikasi akhir
    out = slow(s, "show vlan brief", 14)
    ok10 = bool(re.search(r"^10\s+\S+", out, re.M))
    ok20 = bool(re.search(r"^20\s+\S+", out, re.M))
    print(f" [ ] vlan 10={ok10} vlan 20={ok20}")
    out = slow(s, "show interfaces trunk", 12)
    print(" [ ] trunk Gi0/0:", "ya" if "Gi0/0" in out else "TIDAK")
    s.close()
    print()

print("=== REPAIR SELESAI ===")