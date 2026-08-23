"""Konfigurasi penuh SW1/SW2 (IDE) + verifikasi flash + simpan."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().-]+[#>]\s*$")


def recv_all(s, wait=2.0):
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


def wait_prompt(s, timeout=90):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        chunk = clean(recv_all(s, 1.5))
        if chunk:
            buf += chunk
            lines = [l.strip() for l in buf.splitlines() if l.strip()]
            if lines and PROMPT_RE.search(lines[-1]):
                return buf, lines[-1]
        else:
            s.send(b"\r")
    return buf, ""


def send_raw(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")


def cmd(s, c, timeout=120):
    send_raw(s, c)
    out, _ = wait_prompt(s, timeout)
    bad = any(k in out for k in ("Invalid", "Incomplete", "% "))
    print(" [" + ("X" if bad else " ") + "] " + c)
    return out


def connect_and_enable(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 4)
    send_raw(s, "")
    wait_prompt(s, 30)
    send_raw(s, "enable")
    out, _ = wait_prompt(s, 15)
    if "Password" in out:
        send_raw(s, "Admin123!")
        wait_prompt(s, 15)
    cmd(s, "terminal length 0")
    return s


CFG = {
    "SW1": dict(port=5002,
                vlans=[("10", "USERS-A"), ("20", "SERVERS-A")],
                svi=("interface Vlan10", "ip address 192.168.10.2 "
                     "255.255.255.0", "no shutdown"),
                gw="192.168.10.1"),
    "SW2": dict(port=5004,
                vlans=[("10", "USERS-B"), ("20", "SERVERS-B")],
                svi=("interface Vlan10", "ip address 192.168.30.2 "
                     "255.255.255.0", "no shutdown"),
                gw="192.168.30.1"),
}

for name, cfg in CFG.items():
    print("=" * 22, name, "=" * 22)
    s = socket.create_connection((VM, cfg["port"]), timeout=10)
    s.settimeout(0.5)
    print(" [i] menunggu prompt IOS (boot)...")
    t0 = time.time()
    while time.time() - t0 < 420:
        chunk = clean(recv_all(s, 2))
        if "Press RETURN" in chunk or "Switch>" in chunk or "#" in chunk:
            break
    send_raw(s, "")
    wait_prompt(s, 60)
    send_raw(s, "enable")
    out, _ = wait_prompt(s, 15)
    if "Password" in out:
        send_raw(s, "Admin123!")
        wait_prompt(s, 15)
    cmd(s, "terminal length 0")

    print("--- flash check ---")
    o = cmd(s, "dir flash:", 60)
    good = not ("No such device" in o or "Error" in o)
    print("   [FLASH]", "OK - bisa dibaca!" if good else "MASIH RUSAK")
    if not good:
        s.close()
        continue

    cmd(s, "configure terminal")
    cmd(s, "hostname " + name)
    cmd(s, "enable secret Admin123!")
    cmd(s, "username admin privilege 15 secret Admin123!")
    cmd(s, "ip domain-name lab.local")
    cmd(s, "ip ssh version 2")
    cmd(s, "ip ssh time-out 60")
    cmd(s, "line vty 0 4")
    cmd(s, "login local")
    cmd(s, "transport input ssh")
    cmd(s, "exit")
    for vid, vname in cfg["vlans"]:
        cmd(s, f"vlan {vid}")
        cmd(s, f"name {vname}")
        cmd(s, "exit")
    cmd(s, "interface GigabitEthernet0/0")
    cmd(s, "switchport trunk encapsulation dot1q")
    cmd(s, "switchport mode trunk")
    cmd(s, "exit")
    cmd(s, "interface GigabitEthernet0/1")
    cmd(s, "switchport mode access")
    cmd(s, "switchport access vlan 10")
    cmd(s, "exit")
    cmd(s, "interface GigabitEthernet0/2")
    cmd(s, "switchport mode access")
    cmd(s, "switchport access vlan 20")
    cmd(s, "exit")
    cmd(s, cfg["svi"][0])
    cmd(s, cfg["svi"][1])
    cmd(s, cfg["svi"][2])
    cmd(s, "exit")
    cmd(s, "ip default-gateway " + cfg["gw"])
    cmd(s, "end")
    # crypto key butuh hostname+domain sudah ada
    o = cmd(s, "crypto key generate rsa", 60)
    if "[confirm]" in o or "How many" in o.lower() or "bits" in o.lower():
        send_raw(s, "1024")
        wait_prompt(s, 60)
    cmd(s, "write memory", 240)

    print("--- verifikasi ---")
    o = cmd(s, "show vlan brief", 150)
    ok10 = bool(re.search(r"^10\s+\S+", "\n".join(o.splitlines()), re.M))
    ok20 = bool(re.search(r"^20\s+\S+", "\n".join(o.splitlines()), re.M))
    o = cmd(s, "show interfaces trunk", 90)
    tr = "Gi0/0" in o
    o = cmd(s, "show running-config | include hostname|access vlan",
            90)
    print(f"   [RESULT] vlan10={ok10} vlan20={ok20} trunk={tr}")
    s.close()

print("")
print("=== KONFIGURASI SELESAI ===")