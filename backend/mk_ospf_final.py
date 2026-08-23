"""Template OSPF MK-1 via exec_command (andal) -> verifikasi adjacency."""
import re
import time
import paramiko


def clean(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


def exec_ok(c, cmd, t=30):
    i, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace").strip()
    cl = clean(out)
    badlines = [l for l in cl.splitlines()
                if any(k in l.lower() for k in
                       ["does not match", "failure", "bad command",
                        "expected end"])]
    ok = not badlines and not err
    print(("  X " if not ok else "  OK ") + cmd[:75])
    if not ok:
        print("     !!", (err or badlines[0])[:160])
    return cl


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)

print("=== template OSPF ===")
for net, pasif in [("10.255.10.0/30", "no"), ("10.255.20.0/30", "no"),
                   ("192.168.100.0/24", "yes")]:
    cmd = ("/routing ospf interface-template add instance=lab networks="
           + net + " area=bk2")
    if pasif == "yes":
        cmd += " passive=yes"
    exec_ok(c, cmd)

print("=== verifikasi template tersimpan ===")
out = exec_ok(c, "/routing ospf interface-template print")
body = "\n".join(l for l in out.splitlines() if l.strip())
print(body[-600:])
c.close()

print("")
print("=== tunggu adjacency 35s ===")
time.sleep(35)

print("--- neighbor di MK-1 ---")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)
out = exec_ok(c, "/routing ospf neighbor print")
print("\n".join(l for l in out.splitlines() if l.strip())[-500:])
c.close()

print("")
print("--- neighbor di R1 ---")
r = paramiko.SSHClient()
r.set_missing_host_key_policy(paramiko.AutoAddPolicy())
r.connect("172.22.45.249", username="admin", password="Admin123!", timeout=15,
          allow_agent=False, look_for_keys=False)
sh = r.invoke_shell()
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)
sh.send(b"terminal length 0\n")
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)
sh.send(b"show ip ospf neighbor\n")
time.sleep(8)
out = ""
while sh.recv_ready():
    out += sh.recv(65535).decode(errors="replace")
    time.sleep(0.3)
print("\n".join(l.rstrip() for l in out.splitlines()
                if l.strip() and ("FULL" in l or "Neighbor" in l)))
r.close()