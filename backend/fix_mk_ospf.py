"""Fix OSPF MK-1: buat area backbone eksplisit lalu template."""
import re
import time
import paramiko


def clean(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)
sh = c.invoke_shell()
time.sleep(2)
while sh.recv_ready():
    sh.recv(65535)


def send(cmd, wait=3):
    sh.send(cmd.encode() + b"\n")
    time.sleep(wait)
    out = ""
    while sh.recv_ready():
        out += sh.recv(65535).decode(errors="replace")
        time.sleep(0.2)
    return clean(out)


def run(label, cmd, wait=4):
    out = send(cmd, wait)
    err = [l for l in out.splitlines()
           if ("does not match" in l or "failure" in l.lower()
               or "bad command" in l or "expected" in l)]
    print(("  X " if err else "  OK ") + label)
    if err:
        print("     !!", err[0].strip()[:150])
    return out


print("=== 1. buat area backbone ===")
run("area backbone", "/routing ospf area add instance=lab name=backbone")

print("=== 2. template interface ===")
for net, pasif in [("10.255.10.0/30", "no"), ("10.255.20.0/30", "no"),
                   ("192.168.100.0/24", "yes")]:
    run(net, "/routing ospf interface-template add instance=lab networks="
        + net + " area=backbone passive=" + pasif)

print("=== 3. konfirmasi ===")
out = send("/routing ospf area print", 3)
print("\n".join(l for l in out.splitlines() if l.strip())[-300:])
out = send("/routing ospf interface-template print", 3)
print("\n".join(l for l in out.splitlines() if l.strip())[-600:])

print("")
print("=== 4. tunggu adjacency 30s ===")
time.sleep(30)
out = send("/routing ospf neighbor print", 5)
print(out[-500:])
c.close()