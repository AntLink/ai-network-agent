"""Verifikasi kabel Phase 0 via SSH langsung ke semua device."""
import paramiko
import time
import re


def ios_cmd(client, cmd, wait=2.5):
    sh = client.invoke_shell()
    time.sleep(1)
    while sh.recv_ready():
        sh.recv(65535)
    sh.send(cmd + "\n")
    time.sleep(wait)
    out = ""
    while sh.recv_ready():
        out += sh.recv(65535).decode(errors="replace")
        time.sleep(0.1)
    sh.close()
    lines = [l.rstrip() for l in out.splitlines()
             if l.strip() and not l.strip().startswith(cmd)]
    return "\n".join(lines)


def routeros_cmd(client, cmd, wait=2.5):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode(errors="replace")
    return "\n".join(l.rstrip() for l in out.splitlines() if l.strip())


def connect(host, user="admin", pw="Admin123!"):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, username=user, password=pw, timeout=12,
              allow_agent=False, look_for_keys=False)
    return c


print("=" * 60)
print("R1 (172.22.45.249)")
print("=" * 60)
try:
    c = connect("172.22.45.249")
    print(ios_cmd(c, "show ip interface brief | exclude unassigned"))
    print("\nCDP neighbors:")
    print(ios_cmd(c, "show cdp neighbors", 4))
    c.close()
except Exception as e:
    print("GAGAL:", type(e).__name__, e)

print("\n" + "=" * 60)
print("R2 (172.22.36.184)")
print("=" * 60)
try:
    c = connect("172.22.36.184")
    print(ios_cmd(c, "show ip interface brief | exclude unassigned"))
    print("\nCDP neighbors:")
    print(ios_cmd(c, "show cdp neighbors", 4))
    c.close()
except Exception as e:
    print("GAGAL:", type(e).__name__, e)

print("\n" + "=" * 60)
print("SW1 (172.22.38.10)")
print("=" * 60)
try:
    c = connect("172.22.38.10")
    print(ios_cmd(c, "show interfaces status"))
    print("\nCDP neighbors:")
    print(ios_cmd(c, "show cdp neighbors", 4))
    c.close()
except Exception as e:
    print("GAGAL:", type(e).__name__, e)

print("\n" + "=" * 60)
print("MK-1 (172.22.37.62)")
print("=" * 60)
try:
    c = connect("172.22.37.62", "admin", "admin")
    print(routeros_cmd(c, "/interface/print detail where type=ether"))
    print("\nIP neighbors:")
    print(routeros_cmd(c, "/ip/neighbor/print detail"))
    c.close()
except Exception as e:
    print("GAGAL:", type(e).__name__, e)