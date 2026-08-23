"""Verifikasi akhir Fase 2: routes + ping end-to-end antar PC."""
import re
import socket
import time
import paramiko


def clean_ros(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


def exec_run(c, cmd, t=30):
    i, o, e = c.exec_command(cmd, timeout=t)
    out = clean_ros(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace").strip()
    return out, err


print("=== ROUTE OSPF di MK-1 ===")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)
out, _ = exec_run(c, "/ip route print detail where ospf")
for l in out.splitlines():
    if "o " in l[:6] or "dst-address" in l or "gateway" in l.lower() \
       and "immediate" not in l:
        pass
lines = [l.rstrip() for l in out.splitlines() if l.strip()]
print("\n".join(lines[-14:]))
c.close()

print("")
print("=== NEIGHBOR + ROUTE di R1 ===")
r = paramiko.SSHClient()
r.set_missing_host_key_policy(paramiko.AutoAddPolicy())
r.connect("172.22.45.249", username="admin", password="Admin123!", timeout=15,
          allow_agent=False, look_for_keys=False)
sh = r.invoke_shell()
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)


def cs(cmd, wait=6):
    sh.send(cmd.encode() + b"\n")
    time.sleep(wait)
    out = ""
    while sh.recv_ready():
        out += sh.recv(65535).decode(errors="replace")
        time.sleep(0.25)
    return out


cs("terminal length 0", 2)
out = cs("show ip ospf neighbor", 8)
for l in out.splitlines():
    if "FULL" in l:
        print("   " + l.rstrip())
out = cs("show ip route ospf", 8)
print("   --- route OSPF R1 ---")
for l in out.splitlines():
    if l.strip().startswith("O"):
        print("   " + l.rstrip())
r.close()

# ---------- PING END-TO-END dari VPCS ----------
VM = "172.22.37.68"


def recv_all(s, wait=3.0):
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


def vpcs_ping(port, target, label):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    recv_all(s, 2)
    s.send(b"\r")
    recv_all(s, 1)
    cmd = f"ping {target} -c 3".encode()
    for ch in cmd:
        s.send(bytes([ch]))
        time.sleep(0.02)
    s.send(b"\r")
    out = recv_all(s, 12)
    ok = out.count("bytes from") if "bytes from" in out else \
        len(re.findall(r"icmp_seq=\d+ ttl=", out))
    print(f"   {label:<22} -> {target:<16} balasan: {ok}/3")
    s.close()


print("")
print("=== PING END-TO-END ANTAR SITUS ===")
vpcs_ping(5010, "192.168.100.10", "PC-A1 -> PC-M")     # LAN-A VLAN10 ke LAN-M
vpcs_ping(5014, "192.168.100.10", "PC-B1 -> PC-M")     # LAN-B VLAN10 ke LAN-M
vpcs_ping(5010, "192.168.30.10", "PC-A1 -> PC-B1")     # lintas situs A->B
vpcs_ping(5012, "192.168.30.10", "PC-A2(V20) -> PC-B1")  # VLAN20 A -> B
print("")
print("=== FASE 2 VERIFIKASI SELESAI ===")