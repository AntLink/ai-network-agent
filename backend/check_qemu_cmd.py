"""Cek ukuran disk + cmdline qemu untuk SW1/SW2."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)

cmds = [
    "ls -lh /opt/gns3/projects/a6967457-f60e-4752-be8f-6b66e925245c/project-files/qemu/*/hda_disk.qcow2",
    "ps aux | grep -i qemu | grep -v grep | head -12",
]
for cmd in cmds:
    i, o, e = c.exec_command(cmd, timeout=30)
    print(">>>", cmd)
    print(o.read().decode(errors="replace"))
c.close()