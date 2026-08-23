"""FASE 2: Konfigurasi OSPF area 0 pada R1, R2 (Cisco) dan MK-1 (RouterOS 7)."""
import re
import time
import paramiko


def ssh_connect(ip, user, pw):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(ip, username=user, password=pw, timeout=15,
              allow_agent=False, look_for_keys=False)
    return c


def cisco_send(sh, cmd, wait=2.5):
    sh.send(cmd + "\n")
    time.sleep(wait)
    out = ""
    while sh.recv_ready():
        out += sh.recv(65535).decode(errors="replace")
        time.sleep(0.2)
    bad = ("Invalid" in out) or ("Incomplete" in out)
    print("  [" + ("X" if bad else " ") + "] " + cmd)
    return out


def cisco_ospf(ip, rid, nets, passives):
    print("=== " + ip + " (router-id " + rid + ") ===")
    c = ssh_connect(ip, "admin", "Admin123!")
    sh = c.invoke_shell()
    time.sleep(2)
    while sh.recv_ready():
        sh.recv(65535)
    cisco_send(sh, "terminal length 0")
    cisco_send(sh, "configure terminal")
    cisco_send(sh, "router ospf 1", wait=3)
    cisco_send(sh, "router-id " + rid)
    for n, m in nets:
        cisco_send(sh, "network " + n + " " + m + " area 0")
    for p in passives:
        cisco_send(sh, "passive-interface " + p)
    cisco_send(sh, "end")
    out = cisco_send(sh, "write memory", wait=8)
    print("  [*] simpan:", "OK" if "OK" in out else "PERIKSA")
    c.close()


def ros_exec(c, cmd, wait=2):
    i, o, e = c.exec_command(cmd, timeout=30)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace").strip()
    clean = re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", out)
    bad = ("bad command" in clean) or ("failure" in clean.lower()) or err
    print("  [" + ("X" if bad else " ") + "] " + cmd)
    if bad:
        print("      !!", (err or clean.strip())[:150])
    return clean


print("========== R1 ==========")
cisco_ospf(
    "172.22.45.249", "1.1.1.1",
    [("10.255.10.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
     ("192.168.10.0", "0.0.0.255"), ("192.168.20.0", "0.0.0.255")],
    ["GigabitEthernet0/1.10", "GigabitEthernet0/1.20"],
)

print("")
print("========== R2 ==========")
cisco_ospf(
    "172.22.36.184", "2.2.2.2",
    [("10.255.20.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
     ("192.168.30.0", "0.0.0.255"), ("192.168.40.0", "0.0.0.255")],
    ["GigabitEthernet0/1.10", "GigabitEthernet0/1.20"],
)

print("")
print("========== MK-1 ==========")
c = ssh_connect("172.22.37.168", "admin", "admin")
ros_exec(c, "/routing ospf instance set [find name=\"default\"] router-id=3.3.3.3")
ros_exec(c, "/routing ospf interface-template remove [find]")
for net, pasif in [("10.255.10.0/30", "no"), ("10.255.20.0/30", "no"),
                   ("192.168.100.0/24", "yes")]:
    cmd = ("/routing ospf interface-template add networks=" + net +
           " area=backbone passive=" + pasif)
    ros_exec(c, cmd)
print("  menunggu adjacency (25s)...")
time.sleep(25)
c.close()

# ---------- VERIFIKASI ----------
print("")
print("========== VERIFIKASI NEIGHBOR ==========")

c = ssh_connect("172.22.45.249", "admin", "Admin123!")
sh = c.invoke_shell()
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)
out = cisco_send(sh, "show ip ospf neighbor", wait=8)
print(out[out.find("Neighbor"):][:400] if "Neighbor" in out else out[-300:])
out = cisco_send(sh, "show ip route ospf | include O ", wait=6)
print("--- route OSPF R1 ---")
for l in out.splitlines():
    if l.strip().startswith("O"):
        print("   " + l.rstrip())
c.close()

print("")
c = ssh_connect("172.22.37.168", "admin", "admin")
nb = ros_exec(c, "/routing ospf neighbor print", wait=4)
print(nb[-500:])
rt = ros_exec(c, "/ip route print where ospf", wait=4)
print("--- route OSPF MK ---")
for l in rt.splitlines():
    if "ospf" in l.lower() or "Columns" in l:
        print("   " + l.rstrip())
c.close()
print("")
print("=== FASE 2 SELESAI ===")