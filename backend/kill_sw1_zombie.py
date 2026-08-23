"""Bunuh qemu SW1 zombie di GNS3 VM."""
import time
import paramiko

VM = "172.22.37.68"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(VM, username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)


def run(cmd, t=20):
    i, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace").strip()
    return out.strip(), err


# daftar semua qemu + nama node
out, _ = run("ps -eo pid,args | grep 'qemu-system' | grep -v grep | "
             "sed 's/-drive file=.*uuid/-uuid/' ")
print("=== proses qemu aktif ===")
for l in out.splitlines():
    parts = l.split(None, 1)
    name = ""
    if "-name" in l:
        name = l.split("-name")[1].split()[0]
    print(f"PID={parts[0]:<8} NODE={name:<8}")

print("")
print("=== siapa pegang port 5002 ===")
out, err = run("echo gns3 | sudo -S ss -tlnp 2>/dev/null | grep ':5002'")
print(out if out else "(tidak terbaca)")
print("")

# bunuh SEMUA qemu bernama SW1 (zombie + percobaan baru)
out, _ = run("pgrep -f -- '-name SW1'")
pids = [p for p in out.split() if p.isdigit()]
print("=== kill qemu SW1:", pids, "===")
for pid in pids:
    o_, e_ = run(f"echo gns3 | sudo -S kill -9 {pid} 2>/dev/null;"
                 f" sleep 1; kill -9 {pid} 2>/dev/null && echo killed {pid}"
                 f" || echo sudah-mati {pid}")
    print(" ", o_)

time.sleep(2)
out, _ = run("ps -eo pid,args | grep 'qemu-system' | grep -v grep | "
             "grep -c 'name SW1' || true")
print("")
print("sisa qemu SW1:", out or "0")
out, _ = run("echo gns3 | sudo -S ss -tlnp 2>/dev/null | grep ':5002' || "
             "echo 'port 5002 bebas'")
print(out)
c.close()