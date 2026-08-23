"""Uji atomik: add + count dalam satu eksekusi."""
import re
import time
import paramiko


def clean(t):
    return re.sub(chr(27) + r"\[[0-9;]*[A-Za-z]", "", t)


c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.168", username="admin", password="admin", timeout=15,
          allow_agent=False, look_for_keys=False)

tests = [
    ":put INST=[/routing ospf instance find]",
    ("/routing ospf area add name=bk2 instance=lab\n"
     ":put CNT_AFTER_ADD=[/routing ospf area print count-only]\n"),
    ":put AREA_LIST=[/routing ospf area find]",
]
for cmd in tests:
    i, o, e = c.exec_command(cmd, timeout=30)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace").strip()
    cl = clean(out)
    print(">> CMD:", cmd.replace("\n", " ; ")[:80])
    body = "\n".join(l for l in cl.splitlines() if l.strip())
    print(body[-350:])
    if err:
        print("   ERR:", err[:200])
    print("-" * 50)

# cek juga lewat print biasa setelahnya
time.sleep(3)
i, o, e = c.exec_command("/routing ospf area print", timeout=25)
print(clean(o.read().decode(errors="replace"))[-300:])
c.close()