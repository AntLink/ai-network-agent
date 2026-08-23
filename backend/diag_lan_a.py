"""Triangulasi jalur LAN-A: SW1 (trunk/vlan/mac) + R1 (ping PC)."""
import re
import socket
import time
import paramiko


print("=== SW1: trunk / vlan / mac ===")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.38.10", username="admin", password="Admin123!", timeout=15,
          allow_agent=False, look_for_keys=False)
sh = c.invoke_shell()
time.sleep(3)
while sh.recv_ready():
    sh.recv(65535)


def cs(cmd, wait=8):
    sh.send(cmd.encode() + b"\n")
    time.sleep(wait)
    o_ = ""
    while sh.recv_ready():
        o_ += sh.recv(65535).decode(errors="replace")
        time.sleep(0.3)
    return o_


cs("terminal length 0", 2)
for cmd in ["show interfaces trunk",
            "show vlan brief",
            "show mac address-table dynamic"]:
    out = cs(cmd, 12)
    print(">> " + cmd)
    keep = [l.rstrip() for l in out.splitlines()
            if l.strip() and "show " not in l][:16]
    print("\n".join(keep))
    print("-" * 50)
c.close()

print("")
print("=== R1: ping PC-A1 & PC-A2 ===")
r = paramiko.SSHClient()
r.set_missing_host_key_policy(paramiko.AutoAddPolicy())
r.connect("172.22.45.249", username="admin", password="Admin123!", timeout=15,
          allow_agent=False, look_for_keys=False)
sh = r.invoke_shell()
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)
cs("terminal length 0", 2)


def rate(out):
    m = re.search(r"Success rate is \((\d+)/(\d+)\)", out)
    return f"{m.group(1)}/{m.group(2)}" if m else "?"


out = cs("ping 192.168.10.10 source GigabitEthernet0/1.10 repeat 3", 18)
print("R1 -> PC-A1 :", rate(out))
out = cs("ping 192.168.20.10 source GigabitEthernet0/1.20 repeat 3", 18)
print("R1 -> PC-A2 :", rate(out))
out = cs("show ip arp | include 192.168.1", 8)
for l in out.splitlines():
    if "192.168." in l:
        print("   ARP:", l.rstrip())
r.close()

# PC-A2 ping gateway-nya
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


s = socket.create_connection((VM, 5012), timeout=10)
s.settimeout(1)
recv_all(s, 2)
s.send(b"\r")
recv_all(s, 1)
cmd = b"ping 192.168.20.1"
for ch in cmd:
    s.send(bytes([ch]))
    time.sleep(0.02)
s.send(b"\r")
out = recv_all(s, 15)
n = len(re.findall(r"icmp_seq=\d+ ttl=", out))
print("")
print(f"PC-A2 -> GW (192.168.20.1): {n}/4")
s.close()