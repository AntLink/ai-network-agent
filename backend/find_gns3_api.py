"""Cari port API gns3server di VM + coba akses tanpa auth."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)

cmds = [
    "sudo ss -tlnp | grep -i gns3 || ss -tlnp | grep -E '308|8000'",
    "curl -s -m 5 http://127.0.0.1:3083/v2/version && echo",
    "curl -s -m 5 http://127.0.0.1:30880/v2/version && echo",
]
for cmd in cmds:
    i, o, e = c.exec_command(cmd, timeout=30)
    print(">>>", cmd[:60])
    print(o.read().decode(errors="replace"))
c.close()