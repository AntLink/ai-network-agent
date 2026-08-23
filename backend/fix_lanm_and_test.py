"""Fix template LAN-M + tes berlapis gateway -> lintas situs."""
import re
import socket
import time
import paramiko


def clean_ros(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


print("=== tambah template LAN-M (tanpa passive) ===")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)
i, o, e = c.exec_command(
    "/routing ospf interface-template add networks=192.168.100.0/24 area=bk2",
    timeout=25)
out = clean_ros(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace").strip()
print("OK" if not err and "invalid" not in out and "expected" not in out
      else "GAGAL: " + (err or out)[:120])

time.sleep(20)

i, o, e = c.exec_command("/ip route print where ospf", timeout=25)
out = clean_ros(o.read().decode(errors="replace"))
mk_has_100 = any("192.168.100" not in x for x in [])  # placeholder
lanm_adv = None
c.close()

print("")
print("=== cek route 192.168.100.0 dari R1 ===")
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
    o_ = ""
    while sh.recv_ready():
        o_ += sh.recv(65535).decode(errors="replace")
        time.sleep(0.25)
    return o_


cs("terminal length 0", 2)
out = cs("show ip route ospf | include 192.168.100", 8)
found = [l.rstrip() for l in out.splitlines() if "192.168.100" in l]
print(found[0] if found else "(belum ada - tunggu / cek lagi)")
r.close()

# ---------- tes ping VPCS berlapis ----------
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
    cmd = f"ping {target}".encode()          # tanpa opsi, default 4x
    for ch in cmd:
        s.send(bytes([ch]))
        time.sleep(0.02)
    s.send(b"\r")
    out = recv_all(s, 15)
    replies = len(re.findall(r"icmp_seq=\d+ ttl=", out))
    print(f"   {label:<26} -> {target:<16} {replies}/4")
    if replies == 0:
        tail = [l.strip() for l in out.splitlines() if l.strip()][-3:]
        print("      raw:", " | ".join(tail)[:120])
    s.close()


print("")
print("=== PING BERLAPIS ===")
vpcs_ping(5010, "192.168.10.1", "PC-A1 -> GW sendiri")
vpcs_ping(5018, "192.168.100.1", "PC-M -> GW sendiri")
vpcs_ping(5010, "192.168.30.10", "PC-A1 -> PC-B1")
vpcs_ping(5010, "192.168.100.10", "PC-A1 -> PC-M")