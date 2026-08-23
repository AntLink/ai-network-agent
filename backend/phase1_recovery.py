"""RECOVERY R1 & R2 - tangani initial config dialog dengan benar."""
import socket
import time
import re

VM = "172.22.37.68"

TARGETS = {
    "R1": dict(port=5006, mgmt="172.22.45.249"),
    "R2": dict(port=5008, mgmt="172.22.36.184"),
}

IFACES = {
    "R1": [
        "interface GigabitEthernet0/0",
        "description MGMT-OOB",
        "ip address 172.22.45.249 255.255.240.0",
        "no shutdown", "exit",
        "interface GigabitEthernet0/1",
        "description TRUNK-LAN-A",
        "no shutdown", "exit",
        "interface GigabitEthernet0/1.10",
        "encapsulation dot1Q 10",
        "ip address 192.168.10.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/1.20",
        "encapsulation dot1Q 20",
        "ip address 192.168.20.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/2",
        "description WAN-TO-MK1",
        "ip address 10.255.10.2 255.255.255.252",
        "no shutdown", "exit",
        "interface GigabitEthernet0/3",
        "description BACKUP-TO-R2",
        "ip address 10.255.12.1 255.255.255.252",
        "no shutdown", "exit",
    ],
    "R2": [
        "interface GigabitEthernet0/0",
        "description MGMT-OOB",
        "ip address 172.22.36.184 255.255.240.0",
        "no shutdown", "exit",
        "interface GigabitEthernet0/1",
        "description TRUNK-LAN-B",
        "no shutdown", "exit",
        "interface GigabitEthernet0/1.10",
        "encapsulation dot1Q 10",
        "ip address 192.168.30.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/1.20",
        "encapsulation dot1Q 20",
        "ip address 192.168.40.1 255.255.255.0", "exit",
        "interface GigabitEthernet0/2",
        "description WAN-TO-MK1",
        "ip address 10.255.20.2 255.255.255.252",
        "no shutdown", "exit",
        "interface GigabitEthernet0/3",
        "description BACKUP-TO-R1",
        "ip address 10.255.12.2 255.255.255.252",
        "no shutdown", "exit",
    ],
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
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt


def slow(s, cmd, wait=1.5):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    out = clean(recv_all(s, wait))
    bad = ("Invalid" in out) or ("Incomplete" in out) or ("yes/no" in out)
    print(f" [{'X' if bad else ' '}] {cmd}")
    return out


def clear_dialog(s):
    """Provokasi konsol sampai prompt normal muncul."""
    for attempt in range(12):
        s.send(b"\r\n")
        out = recv_all(s, 2)
        if "[yes/no]" in out:
            s.send(b"no\r")
            recv_all(s, 3)
            continue
        if re.search(r"[>#]\s*$", out.strip()):
            print(" [ ] dialog bersih, prompt normal")
            return True
    return False


def config(name, info):
    port = info["port"]
    print(f"\n===== {name} ({VM}:{port}) =====")
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    recv_all(s, 2)

    if not clear_dialog(s):
        print(" GAGAL membersihkan dialog!")
        s.close()
        return False

    slow(s, "enable", 2)
    slow(s, "terminal length 0", 1)
    slow(s, "configure terminal")
    slow(s, f"hostname {name}")
    slow(s, "enable secret Admin123!")
    slow(s, "username admin privilege 15 secret Admin123!")
    slow(s, "ip domain-name lab.local")
    out = slow(s, "crypto key generate rsa modulus 2048", wait=9)
    if "confirm" in out.lower() or "[yes/no]" in out:
        s.send(b"\r")
        recv_all(s, 8)
    slow(s, "ip ssh version 2")
    slow(s, "line vty 0 4")
    slow(s, "login local")
    slow(s, "privilege level 15")
    slow(s, "transport input ssh")
    slow(s, "exit")

    for cmd in IFACES[name]:
        slow(s, cmd)

    slow(s, "end")
    out = slow(s, "write memory", wait=7)
    ok = ("OK" in out) or ("Building" in out)
    print(f" [*] write memory -> {'OK' if ok else 'PERIKSA'}")
    s.close()
    return ok


if __name__ == "__main__":
    results = {}
    for name, info in TARGETS.items():
        results[name] = config(name, info)
    print("\nREKAP:", results)