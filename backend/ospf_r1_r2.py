"""OSPF untuk R1 & R2 via SSH + tunggu adjacency."""
import time
import paramiko


def ssh_connect(ip, user, pw):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(ip, username=user, password=pw, timeout=15,
              allow_agent=False, look_for_keys=False)
    return c


def cisco_send(sh, cmd, wait=3):
    sh.send(cmd + "\n")
    time.sleep(wait)
    out = ""
    while sh.recv_ready():
        out += sh.recv(65535).decode(errors="replace")
        time.sleep(0.25)
    bad = ("Invalid" in out) or ("Incomplete" in out)
    print("  [" + ("X" if bad else " ") + "] " + cmd)
    return out


def ospf_push(ip, rid, nets):
    print("=== OSPF " + ip + " (" + rid + ") ===")
    c = ssh_connect(ip, "admin", "Admin123!")
    sh = c.invoke_shell()
    time.sleep(2)
    while sh.recv_ready():
        sh.recv(65535)
    cisco_send(sh, "terminal length 0")
    cisco_send(sh, "configure terminal")
    cisco_send(sh, "router ospf 1")
    cisco_send(sh, "router-id " + rid)
    for n, m in nets:
        cisco_send(sh, "network " + n + " " + m + " area 0")
    cisco_send(sh, "passive-interface GigabitEthernet0/1.10")
    cisco_send(sh, "passive-interface GigabitEthernet0/1.20")
    cisco_send(sh, "end")
    o = cisco_send(sh, "write memory", 8)
    print("  [*] simpan:", "OK" if "OK" in o else "PERIKSA")
    c.close()


ospf_push("172.22.45.249", "1.1.1.1",
          [("10.255.10.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
           ("192.168.10.0", "0.0.0.255"), ("192.168.20.0", "0.0.0.255")])
print("")
ospf_push("172.22.36.184", "2.2.2.2",
          [("10.255.20.0", "0.0.0.3"), ("10.255.12.0", "0.0.0.3"),
           ("192.168.30.0", "0.0.0.255"), ("192.168.40.0", "0.0.0.255")])

print("")
print("menunggu adjacency penuh 45s...")
time.sleep(45)

print("")
print("=== neighbor R1 ===")
c = ssh_connect("172.22.45.249", "admin", "Admin123!")
sh = c.invoke_shell()
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)
cisco_send(sh, "terminal length 0", 1)
o = cisco_send(sh, "show ip ospf neighbor", 8)
for l in o.splitlines():
    if "FULL" in l:
        print("   " + l.rstrip())
o = cisco_send(sh, "show ip route ospf | include ^O", 8)
for l in o.splitlines():
    if l.strip().startswith("O"):
        print("   " + l.rstrip())
c.close()