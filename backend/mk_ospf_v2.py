"""Template OSPF TANPA param instance -> verifikasi penuh."""
import re
import time
import paramiko


def clean(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


def exec_run(c, cmd, t=30):
    i, o, e = c.exec_command(cmd, timeout=t)
    out = clean(o.read().decode(errors="replace"))
    err = e.read().decode(errors="replace").strip()
    return out, err


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)

print("=== add template (tanpa instance=) ===")
adds = [
    "/routing ospf interface-template add networks=10.255.10.0/30 area=bk2",
    "/routing ospf interface-template add networks=10.255.20.0/30 area=bk2",
    "/routing ospf interface-template add networks=192.168.100.0/24 area=bk2 passive=yes",
]
for cmd in adds:
    out, err = exec_run(c, cmd)
    bad = bool(err) or ("invalid" in out or "expected" in out or "match" in out)
    print(("  X " if bad else "  OK ") + cmd[40:])
    if bad:
        print("     !!", (err or out.strip())[:160])

print("=== verifikasi ===")
out, _ = exec_run(c, "/routing ospf interface-template print")
print("\n".join(l for l in out.splitlines() if l.strip())[-500:])
c.close()

print("")
print("=== tunggu adjacency 40s ===")
time.sleep(40)

print("--- neighbor MK-1 ---")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)
out, _ = exec_run(c, "/routing ospf neighbor print")
print("\n".join(l for l in out.splitlines() if l.strip())[-400:])
out, _ = exec_run(c, "/ip route print where ospf")
print("--- route OSPF MK ---")
for l in out.splitlines():
    if "ospf" in l.lower() or "Columns" in l or l.strip().startswith("0") \
       or l.strip().startswith("1"):
        print("   " + l.rstrip())
c.close()