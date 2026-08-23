"""Selidiki submenu OSPF ROS 7.22 + tes add template interaktif."""
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


# probe menu & error messages
for cmd in [
    "/routing ospf print",
    "/routing ospf area print",
    "/routing ospf interface-template add",
    "/routing ospf interface-template add instance=lab networks=10.255.10.0/30 area=backbone",
]:
    out = send(cmd, wait=4)
    print(">> " + cmd)
    tail = [l for l in out.splitlines() if l.strip()][-8:]
    print("\n".join(tail))
    print("-" * 50)

print("")
print("=== cek ulang template ===")
print(send("/routing ospf interface-template print", wait=3)[-300:])
c.close()