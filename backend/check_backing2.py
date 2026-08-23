"""qemu-img info dengan -U (tanpa lock) + isi folder IOS/QEMU."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=15,
          allow_agent=False, look_for_keys=False)

cmds = [
    "ls -lh /opt/gns3/images/IOS/ /opt/gns3/images/QEMU/",
    ("for f in 18bd9697-da5c-41f2-8dd5-483315a7c99d "
     "12adbd8f-7400-4d36-816c-c2b1f0e428b3 "
     "e49bc1fc-27ad-4a70-859b-707d60a63501; do "
     "echo '== '$f; qemu-img info -U --backing-chain /opt/gns3/projects/"
     "a6967457-f60e-4752-be8f-6b66e925245c/project-files/qemu/$f/"
     "hda_disk.qcow2 | grep -E 'image:|backing file|virtual size'; done"),
]
for cmd in cmds:
    i, o, e = c.exec_command(cmd, timeout=60)
    print(">>>", cmd[:70])
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    for l in out.splitlines():
        print("   ", l)
    if err.strip() and "Failed to get shared" not in err:
        print("ERR:", err[:200])
c.close()