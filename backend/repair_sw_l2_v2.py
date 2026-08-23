"""Repair L2 SW1/SW2 versi prompt-synced (anti telan-input)."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().-]+[#>]\s*$")


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
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt


def wait_prompt(s, timeout=60):
    """Baca sampai baris terakhir adalah prompt."""
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


def cmd(s, c, timeout=90):
    """Kirim perintah hanya saat prompt siap; tunggu prompt berikutnya."""
    s.send(c.encode())
    time.sleep(0.03)
    s.send(b"\r")
    out, prompt = wait_prompt(s, timeout)
    bad = any(k in out for k in ("Invalid", "Incomplete", "% "))
    print(" [" + ("X" if bad else " ") + "] " + c + "   -> " + prompt[:28])
    if bad:
        err = [l for l in out.splitlines()
               if any(k in l for k in ("Invalid", "Incomplete"))]
        if err:
            print("     !!", err[0][:120])
    return out


def connect(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 4)
    s.send(b"\r")
    wait_prompt(s, 30)
    # enable
    s.send(b"enable\r")
    out, _ = wait_prompt(s, 15)
    if "Password" in out:
        s.send(b"Admin123!\r")
        wait_prompt(s, 15)
    cmd(s, "terminal length 0")
    return s


REPAIR = {
    "SW1": dict(port=5002,
                vlans=[("10", "USERS-A"), ("20", "SERVERS-A")],
                ports=[("GigabitEthernet0/0", "trunk"),
                       ("GigabitEthernet0/1", "access 10"),
                       ("GigabitEthernet0/2", "access 20")]),
    "SW2": dict(port=5004,
                vlans=[("10", "USERS-B"), ("20", "SERVERS-B")],
                ports=[("GigabitEthernet0/0", "trunk"),
                       ("GigabitEthernet0/1", "access 10"),
                       ("GigabitEthernet0/2", "access 20")]),
}

for name, cfg in REPAIR.items():
    print("=" * 20, name, "=" * 20)
    s = connect(cfg["port"])
    cmd(s, "configure terminal")
    for vid, vname in cfg["vlans"]:
        cmd(s, f"vlan {vid}")
        cmd(s, f"name {vname}")
        cmd(s, "exit")
    for intf, mode in cfg["ports"]:
        cmd(s, "interface " + intf)
        if mode == "trunk":
            cmd(s, "switchport trunk encapsulation dot1q")
            cmd(s, "switchport mode trunk")
        else:
            _, vid = mode.split()
            cmd(s, "switchport mode access")
            cmd(s, f"switchport access vlan {vid}")
        cmd(s, "exit")
    cmd(s, "end")
    cmd(s, "write memory", 120)

    print("--- verifikasi ---")
    o = cmd(s, "show vlan brief", 120)
    ok10 = bool(re.search(r"^10\s+\S+", o, re.M))
    ok20 = bool(re.search(r"^20\s+\S+", o, re.M))
    o2 = cmd(s, "show interfaces trunk", 90)
    tr = "Gi0/0" in o2
    print(f" [RESULT] vlan10={ok10} vlan20={ok20} trunk={tr}")
    s.close()

print("")
print("=== SELESAI ===")