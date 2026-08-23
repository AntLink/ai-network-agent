"""Perbaikan final access-port + simpan + BUKTI startup lengkap."""
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


def send_cmd(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")


def wait_prompt(s, timeout=60):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = clean(recv_all(s, 1.0))
        buf += c
        lines = [l.strip() for l in buf.splitlines() if l.strip()]
        ll = lines[-1] if lines else ""
        if PROMPT_RE.search(ll):
            return buf, ll
    return buf, ""


def ios(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    buf, ll = wait_prompt(s, 20)
    if ll.endswith(">"):
        send_cmd(s, "enable")
        b2, _ = wait_prompt(s, 15)
        if "Password" in b2:
            send_cmd(s, "Admin123!")
            wait_prompt(s, 15)
    send_cmd(s, "terminal length 0")
    wait_prompt(s, 8)
    return s


for name, port in [("SW1", 5002), ("SW2", 5004)]:
    print("=" * 20, name, "=" * 20)
    s = ios(port)

    send_cmd(s, "configure terminal")
    wait_prompt(s, 15)

    send_cmd(s, "interface GigabitEthernet0/1")
    wait_prompt(s, 12)
    send_cmd(s, "switchport mode access")
    wait_prompt(s, 12)
    send_cmd(s, "switchport access vlan 10")
    o, _ = wait_prompt(s, 20)
    if "%" in o:
        print("   !! error di gi0/1:", [l.strip()[:80] for l in
                                        o.splitlines() if "%" in l][:1])
    send_cmd(s, "exit")
    wait_prompt(s, 10)

    send_cmd(s, "interface GigabitEthernet0/2")
    wait_prompt(s, 12)
    send_cmd(s, "switchport mode access")
    wait_prompt(s, 12)
    send_cmd(s, "switchport access vlan 20")
    o, _ = wait_prompt(s, 20)
    if "%" in o:
        print("   !! error di gi0/2:", [l.strip()[:80] for l in
                                        o.splitlines() if "%" in l][:1])
    send_cmd(s, "exit")
    wait_prompt(s, 10)

    send_cmd(s, "end")
    wait_prompt(s, 12)

    send_cmd(s, "write memory")
    o, _ = wait_prompt(s, 120)
    print("   write memory:", "OK" if "[OK]" in o else "CEK!")

    print("--- BUKTI STARTUP ---")
    send_cmd(s, "show startup-config | include access vlan|mode trunk|"
                "hostname")
    o, _ = wait_prompt(s, 45)
    found = []
    for l in o.splitlines():
        ls = l.strip()
        if ls.startswith(("switchport", "hostname")):
            found.append(ls)
            print("   ", ls)
    need = ["mode trunk", "access vlan 10", "access vlan 20",
            f"hostname {name}"]
    missing = [n_ for n_ in need
               if not any(n_ in f_ for f_ in found)]
    print("   [STARTUP]", "LENGKAP!" if not missing else
          f"KURANG: {missing}")

    print("--- vlan brief ---")
    send_cmd(s, "show vlan brief")
    o, _ = wait_prompt(s, 90)
    for l in o.splitlines():
        ls = l.rstrip()
        if re.match(r"^(10|20)\s+\S+\s+active", ls):
            print("   ", ls[:95])
    s.close()

print("")
print("[i] beri 30s untuk STP/ARP settle...")
time.sleep(30)