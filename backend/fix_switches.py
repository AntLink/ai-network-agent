"""Re-konfigurasi SW1 & SW2 (IOSvL2 lambat/crash-prone) dengan timing sabar."""
import socket
import time
import re

VM = "172.22.37.68"
ESC = chr(27)

CONFIGS = {
    "SW1": dict(port=5002, cmds=[
        "hostname SW1",
        "enable secret Admin123!",
        "username admin privilege 15 secret Admin123!",
        "ip domain-name lab.local",
        "crypto key generate rsa modulus 2048",
        "ip ssh version 2",
        "line vty 0 4", "login local", "privilege level 15",
        "transport input ssh", "exit",
        "vlan 10", "name USERS-A", "exit",
        "vlan 20", "name SERVERS-A", "exit",
        "interface GigabitEthernet0/0",
        "description TRUNK-TO-R1",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk", "exit",
        "interface GigabitEthernet0/1",
        "description PC-A1",
        "switchport mode access",
        "switchport access vlan 10", "exit",
        "interface GigabitEthernet0/2",
        "description PC-A2",
        "switchport mode access",
        "switchport access vlan 20", "exit",
        "interface Vlan1",
        "ip address 172.22.38.10 255.255.240.0",
        "no shutdown", "exit",
        "ip default-gateway 172.22.32.1",
    ]),
    "SW2": dict(port=5004, cmds=[
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
    ]),
}


def recv_all(s, wait=6.0):
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
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return "\n".join(l.rstrip() for l in txt.splitlines() if l.strip())


def slow(s, cmd, wait=6):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.04)
    s.send(b"\r")
    out = clean(recv_all(s, wait))
    bad = ("Invalid" in out) or ("Incomplete" in out)
    print(" [" + ("X" if bad else " ") + "] " + cmd)
    if bad:
        print("     !!", [l for l in out.splitlines()
                         if "Invalid" in l or "Incomplete" in l])
    return out


def wait_prompt(s, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s.send(b"\r")
        out = recv_all(s, 5)
        if re.search(r"Switch[>#]", out):
            print(" [ ] prompt Switch> siap")
            return True
        if "[yes/no]" in out:
            s.send(b"no\r")
            continue
    return False


for name, cfg in CONFIGS.items():
    print("")
    print("========== " + name + " (" + VM + ":" + str(cfg["port"]) + ") ==========")
    s = socket.create_connection((VM, cfg["port"]), timeout=10)
    s.settimeout(1)
    recv_all(s, 8)
    if not wait_prompt(s):
        print(" GAGAL: prompt tidak muncul")
        s.close()
        continue

    slow(s, "enable", 8)
    slow(s, "terminal length 0", 8)
    slow(s, "configure terminal", 8)

    for cmd in cfg["cmds"]:
        wait = 25 if cmd.startswith("crypto") else 7
        out = slow(s, cmd, wait=wait)
        if cmd.startswith("crypto") and ("confirm" in out.lower() or "[yes/no]" in out):
            s.send(b"\r")
            recv_all(s, 20)

    slow(s, "end", 8)
    out = slow(s, "write memory", 30)
    ok = ("OK" in out) or ("Building" in out)
    print(" [*] write memory -> " + ("OK" if ok else "PERIKSA"))

    ver = slow(s, "show startup-config | include hostname", 12)
    host = [l for l in ver.splitlines() if "hostname" in l]
    print(" [ ] startup: " + (host[-1] if host else "?"))

    ping = slow(s, "ping 172.22.32.1", 20)
    rate = re.search(r"Success rate is \((\d+)/(\d+)\)", ping)
    print(" [ ] ping gw -> " + (rate.group(0) if rate else "tanpa hasil"))
    s.close()

print("")
print("=== SELESAI ===")