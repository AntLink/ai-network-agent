"""Dump mentah respons add + export konfigurasi OSPF."""
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
    "/routing ospf interface-template add instance=lab networks=10.255.10.0/30 area=bk2",
    "/routing ospf interface-template print",
    "/routing ospf export",
    "/routing ospf instance print",
]:
    i, o, e = c.exec_command(cmd, timeout=30)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace").strip()
    time.sleep(0.5)
    more = b""
    if o.channel.exit_status_ready() is False:
        pass
    cl = clean(out)
    print("=" * 60)
    print(">> " + cmd)
    print("STDOUT:")
    print(repr(cl[-400:]) if len(cl) < 500 else cl[-400:])
    if err:
        print("STDERR:", repr(err[:300]))
c.close()