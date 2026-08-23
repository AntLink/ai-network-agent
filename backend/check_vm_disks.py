"""Cek file disk qcow2 SW1/SW2 di dalam GNS3 VM."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)

cmds = [
    "find /opt/gns3/projects -name '*.qcow2' 2>/dev/null",
    "find /var/lib/gns3 -maxdepth 5 -name '*.qcow2' 2>/dev/null | head -20",
    "ls /opt/gns3/projects/ 2>/dev/null",
]
for cmd in cmds:
    i, o, e = c.exec_command(cmd, timeout=60)
    print(">>>", cmd)
    print(o.read().decode(errors="replace"))
c.close()