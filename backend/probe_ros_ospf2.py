"""Probe ulang: verifikasi via exec_command + counter find."""
import re
import time
import paramiko


def clean(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)

for cmd in [
    ":put AREA=[/routing ospf area find]",
    ":put TMPL=[/routing ospf interface-template find]",
    "/routing ospf area print detail",
    "/routing ospf interface-template print detail",
]:
    i, o, e = c.exec_command(cmd, timeout=25)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace").strip()
    cl = clean(out)
    print(">> " + cmd)
    body = "\n".join(l for l in cl.splitlines() if l.strip())
    print(body[-400:])
    if err:
        print("   ERR:", err[:200])
    print("-" * 50)
c.close()