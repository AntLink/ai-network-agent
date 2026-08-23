"""Verifikasi akhir Fase 2 v2: neighbors/routes via konsol + MK + ping PC."""
import re
import socket
import time
import paramiko

VM = "172.22.37.68"
ESC = chr(27)


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


def slow(s, cmd, wait=8):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    return clean(recv_all(s, wait))


def console_show(port, label, cmds):
    print("==========", label, "==========")
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    recv_all(s, 3)
    slow(s, "", 2)
    slow(s, "enable", 4)
    slow(s, "terminal length 0", 4)
    for cmd, w in cmds:
        out = slow(s, cmd, w)
        for l in out.splitlines():
            ls = l.strip()
            if ("FULL" in ls or ls.startswith("O ")
                    or ls.startswith("O   ") or "Neighbor" in ls):
                print("   " + l.rstrip())
    s.close()


console_show(5006, "R1", [
    ("show ip ospf neighbor", 10),
    ("show ip route ospf | include ^O", 10),
])
print()
console_show(5008, "R2", [
    ("show ip ospf neighbor", 10),
    ("show ip route ospf | include ^O", 10),
])

print()
print("========== MK-1 ==========")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(VM.replace("5002", "5002"), username="admin", password="admin",
          timeout=15, allow_agent=False, look_for_keys=False) \
    if False else c.connect("172.22.37.168", username="admin",
                            password="admin", timeout=15,
                            allow_agent=False, look_for_keys=False)


def ros(cmd, t=25):
    i, o, e = c.exec_command(cmd, timeout=t)
    return re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "",
                  o.read().decode(errors="replace"))


out = ros("/routing ospf neighbor print")
for l in out.splitlines():
    if 'state="Full"' in l or "router-id" in l:
        print("   " + l.strip())
out = ros("/ip route print where ospf")
n = 0
for l in out.splitlines():
    ls = l.strip()
    if re.match(r"^[0-9]+ \s*DAo", ls) or "DAo" in ls:
        n += 1
        dst = ls.split()[1] if len(ls.split()) > 1 else "?"
        gw = "via " + (ls.split("gateway=")[1].split()[0]
                       if "gateway=" in ls else "?")
        print(f"   {dst:<18} {gw}")
print(f"   total rute OSPF MK: {n}")
c.close()

# ---------- PING END-TO-END ----------
print()
print("========== PING ANTAR PC ==========")


def vpcs_ping(port, target, label):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    recv_all(s, 2)
    s.send(b"\r")
    recv_all(s, 1)
    for ch in f"ping {target}":
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")
    out = recv_all(s, 16)
    replies = len(re.findall(r"icmp_seq=\d+ ttl=", out))
    status = "SUKSES" if replies >= 3 else ("sebagian" if replies else "GAGAL")
    print(f"   {label:<24} -> {target:<16} {replies}/4 [{status}]")
    if replies == 0:
        tail = [l.strip() for l in out.splitlines() if l.strip()][-2:]
        print("      raw:", " | ".join(tail)[:100])
    s.close()


vpcs_ping(5010, "192.168.10.1", "PC-A1 -> GW-A")        # lokal
vpcs_ping(5014, "192.168.30.1", "PC-B1 -> GW-B")        # lokal
vpcs_ping(5018, "192.168.100.1", "PC-M -> GW-M")        # lokal
vpcs_ping(5010, "192.168.30.10", "PC-A1 -> PC-B1")      # lintas situs
vpcs_ping(5010, "192.168.100.10", "PC-A1 -> PC-M")      # ke LAN-M
vpcs_ping(5016, "192.168.20.10", "PC-B2 -> PC-A2")      # VLAN20 lintas
print()
print("=== VERIFIKASI SELESAI ===")