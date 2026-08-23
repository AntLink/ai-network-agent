"""Coba SSH ke GNS3 VM dan cari proses pemegang port 5002."""
import time
import paramiko

VM = "172.22.37.68"
CREDS = [("root", "gns3"), ("root", ""), ("root", "root"),
         ("gns3", "gns3"), ("admin", "admin")]

client = None
for u, p in CREDS:
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(VM, username=u, password=p or None, timeout=8,
                  allow_agent=False, look_for_keys=False)
        client = c
        print("LOGIN OK:", u)
        break
    except Exception as e:
        print(f"  gagal {u}/{'(kosong)' if not p else '***'}: "
              f"{type(e).__name__}")

if client:
    for cmd in ["uname -a",
                "ss -tlnp | grep -E ':(500[0-9]|501[0-9])' | head -20",
                "ps aux | grep -i qemu | grep -v grep | head -10"]:
        i, o, e = client.exec_command(cmd, timeout=15)
        out = o.read().decode(errors="replace")
        err = e.read().decode(errors="replace").strip()
        print(">>", cmd)
        print(out.strip()[:1200])
        if err:
            print("[stderr]", err[:200])
    client.close()
else:
    print("TIDAK BISA SSH KE VM")