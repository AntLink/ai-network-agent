"""OSPF R1 & R2 via SSH legacy + verifikasi adjacency."""
import time
from legacy_ssh import connect_legacy, shell_send


def ospf_push(ip, rid, nets):
    print("=== OSPF " + ip + " (" + rid + ") ===")
    c = connect_legacy(ip)
    sh = c.invoke_shell() if hasattr(c, "invoke_shell") else c
    time.sleep(2)
    while sh.recv_ready():
        sh.recv(65535)
    shell_send(sh, "terminal length 0")
    shell_send(sh, "configure terminal")
    shell_send(sh, "router ospf 1")
    shell_send(sh, "router-id " + rid)
    for n, m in nets:
        shell_send(sh, "network " + n + " " + m + " area 0")
    shell_send(sh, "passive-interface GigabitEthernet0/1.10")
    shell_send(sh, "passive-interface GigabitEthernet0/1.20")
    shell_send(sh, "end")
    o = shell_send(sh, "write memory", 8)
    print("  [*] simpan:", "OK" if "OK" in o else "PERIKSA")
    try:
        c.close()
    except Exception:
        if hasattr(sh, "_transport"):
            sh._transport.close()


ospf_push("172.22.45.249", "1.1.1.1",
          [("10.255.10.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
           ("192.168.10.0", "0.0.0.255"), ("192.168.20.0", "0.0.0.255")])
print("")
ospf_push("172.22.36.184", "2.2.2.2",
          [("10.255.20.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
           ("192.168.30.0", "0.0.0.255"), ("192.168.40.0", "0.0.0.255")])

print("")
print("menunggu adjacency 45s...")
time.sleep(45)

print("=== neighbor R1 ===")
c = connect_legacy("172.22.45.249")
sh = c.invoke_shell() if hasattr(c, "invoke_shell") else c
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)
shell_send(sh, "terminal length 0", 2)
o = shell_send(sh, "show ip ospf neighbor", 8)
for l in o.splitlines():
    if "FULL" in l:
        print("   " + l.rstrip())
o = shell_send(sh, "show ip route ospf | include ^O", 8)
for l in o.splitlines():
    if l.strip().startswith("O"):
        print("   " + l.rstrip())
try:
    c.close()
except Exception:
    pass