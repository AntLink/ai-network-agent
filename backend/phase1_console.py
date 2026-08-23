"""PHASE 1 - Base config otomatis seluruh lab via konsol telnet GNS3."""
import socket
import time
import re
import sys

VM = "172.22.37.68"

NODES = {
    "R1":  dict(port=5006, mgmt="172.22.45.249"),
    "R2":  dict(port=5008, mgmt="172.22.36.184"),
    "SW1": dict(port=5002, mgmt="172.22.38.10"),
    "SW2": dict(port=5004, mgmt="172.22.39.10"),
}

PCS = {
    "PC-A1": (5010, "192.168.10.10", "192.168.10.1"),
    "PC-A2": (5012, "192.168.20.10", "192.168.20.1"),
    "PC-B1": (5014, "192.168.30.10", "192.168.30.1"),
    "PC-B2": (5016, "192.168.40.10", "192.168.40.1"),
    "PC-M":  (5018, "192.168.100.10", "192.168.100.1"),
}


def recv_all(s, wait=2.0):
    buf = b""
    start = time.time()
    while time.time() - start < wait:
        try:
            d = s.recv(4096)
            if not d:
                break
            buf += d
            start = time.time()
        except socket.timeout:
            break
    return buf.decode(errors="replace")


def clean(txt):
    txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b\x00-\x1f]", "", txt)
    return txt


def slow(s, cmd, wait=1.2, quiet=False):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    out = clean(recv_all(s, wait))
    if not quiet:
        tail = [l.strip() for l in out.splitlines() if l.strip()][-1:]
        status = tail[0] if tail else ""
        flag = "!" if ("Invalid" in out or "Incomplete" in out) else " "
        print(f" [{flag}] {cmd:<55} {status[:60]}")
    return out


def open_console(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    return s


# ---------------------------------------------------------------- CISCO
def config_cisco(name, info):
    port, mgmt = info["port"], info["mgmt"]
    print(f"\n===== {name} ({VM}:{port}) =====")
    s = open_console(port)
    boot = recv_all(s, 2)

    # keluar dari initial configuration dialog bila muncul
    if "yes/no" in boot or "yes/no" in clean(recv_all(s, 1)):
        slow(s, "no", 3)

    slow(s, "enable", 1.5)
    slow(s, "terminal length 0", 1)

    # ---- blok dasar & manajemen ----
    slow(s, "configure terminal")
    slow(s, f"hostname {name}")
    slow(s, "enable secret Admin123!")
    slow(s, "username admin privilege 15 secret Admin123!")
    slow(s, "ip domain-name lab.local")
    out = slow(s, "crypto key generate rsa modulus 2048", wait=9, quiet=True)
    if "confirm" in out.lower() or "[yes/no]" in out:
        s.send(b"\r")
        recv_all(s, 8)
    print(" [ ] crypto key generate rsa modulus 2048          (RSA keys)")
    slow(s, "ip ssh version 2")
    slow(s, "line vty 0 4")
    slow(s, "login local")
    slow(s, "privilege level 15")
    slow(s, "transport input ssh")
    slow(s, "exit")

    yield_iface = IFACES[name]
    for cmd in yield_iface:
        slow(s, cmd, wait=2 if cmd.startswith(("interface ", "encap")) else 1)

    slow(s, "end")
    out = slow(s, "write memory", wait=7, quiet=True)
    ok = ("OK" in out) or ("Building" in out)
    print(f" [*] write memory -> {'OK' if ok else 'PERIKSA'}")
    s.close()


IFACES = {
    "R1": [
        "interface GigabitEthernet0/0",
        "description MGMT-OOB",
        "ip address 172.22.45.249 255.255.240.0",
        "no shutdown",
        "exit",
        "interface GigabitEthernet0/1",
        "description TRUNK-LAN-A",
        "no shutdown",
        "exit",
        "interface GigabitEthernet0/1.10",
        "encapsulation dot1Q 10",
        "ip address 192.168.10.1 255.255.255.0",
        "exit",
        "interface GigabitEthernet0/1.20",
        "encapsulation dot1Q 20",
        "ip address 192.168.20.1 255.255.255.0",
        "exit",
        "interface GigabitEthernet0/2",
        "description WAN-TO-MK1",
        "ip address 10.255.10.2 255.255.255.252",
        "no shutdown",
        "exit",
        "interface GigabitEthernet0/3",
        "description BACKUP-TO-R2",
        "ip address 10.255.12.1 255.255.255.252",
        "no shutdown",
        "exit",
    ],
    "R2": [
        "interface GigabitEthernet0/0",
        "description MGMT-OOB",
        "ip address 172.22.36.184 255.255.240.0",
        "no shutdown",
        "exit",
        "interface GigabitEthernet0/1",
        "description TRUNK-LAN-B",
        "no shutdown",
        "exit",
        "interface GigabitEthernet0/1.10",
        "encapsulation dot1Q 10",
        "ip address 192.168.30.1 255.255.255.0",
        "exit",
        "interface GigabitEthernet0/1.20",
        "encapsulation dot1Q 20",
        "ip address 192.168.40.1 255.255.255.0",
        "exit",
        "interface GigabitEthernet0/2",
        "description WAN-TO-MK1",
        "ip address 10.255.20.2 255.255.255.252",
        "no shutdown",
        "exit",
        "interface GigabitEthernet0/3",
        "description BACKUP-TO-R1",
        "ip address 10.255.12.2 255.255.255.252",
        "no shutdown",
        "exit",
    ],
    "SW1": [
        "vlan 10",
        "name USERS-A",
        "exit",
        "vlan 20",
        "name SERVERS-A",
        "exit",
        "interface GigabitEthernet0/0",
        "description TRUNK-TO-R1",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk",
        "exit",
        "interface GigabitEthernet0/1",
        "description PC-A1",
        "switchport mode access",
        "switchport access vlan 10",
        "exit",
        "interface GigabitEthernet0/2",
        "description PC-A2",
        "switchport mode access",
        "switchport access vlan 20",
        "exit",
        "interface Vlan1",
        "ip address 172.22.38.10 255.255.240.0",
        "no shutdown",
        "exit",
        "ip default-gateway 172.22.32.1",
    ],
    "SW2": [
        "vlan 10",
        "name USERS-B",
        "exit",
        "vlan 20",
        "name SERVERS-B",
        "exit",
        "interface GigabitEthernet0/0",
        "description TRUNK-TO-R2",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk",
        "exit",
        "interface GigabitEthernet0/1",
        "description PC-B1",
        "switchport mode access",
        "switchport access vlan 10",
        "exit",
        "interface GigabitEthernet0/2",
        "description PC-B2",
        "switchport mode access",
        "switchport access vlan 20",
        "exit",
        "interface Vlan1",
        "ip address 172.22.39.10 255.255.240.0",
        "no shutdown",
        "exit",
        "ip default-gateway 172.22.32.1",
    ],
}


# ---------------------------------------------------------------- PC/VPCS
def config_pc(name, port, ip, gw):
    print(f"\n===== {name} ({VM}:{port}) =====")
    s = open_console(port)
    recv_all(s, 1.5)
    mask = "255.255.255.0"
    slow(s, f"ip {ip} {mask} {gw}", wait=1.5)
    slow(s, "save", wait=1.5)
    out = slow(s, "show ip", wait=1.5, quiet=True)
    for l in clean(out).splitlines():
        if "ip :" in l or "gateway" in l.lower():
            print("   ", l.strip()[:70])
    s.close()


# ---------------------------------------------------------------- MAIN
if __name__ == "__main__":
    only = sys.argv[1:] or list(NODES.keys())
    for name in only:
        config_cisco(name, NODES[name])

    pc_only = sys.argv[1:] or None
    if not pc_only or any(p in sys.argv[1:] for p in PCS) or not sys.argv[1:]:
        for name, (port, ip, gw) in PCS.items():
            config_pc(name, port, ip, gw)

    print("\n=== PHASE 1 CONSOLE SELESAI ===")