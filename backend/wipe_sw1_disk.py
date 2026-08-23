"""Cek proses & file disk SW1/SW2; hapus disk SW1 jika aman."""
import time
import paramiko

PROJ = "a6967457-f60e-4752-be8f-6b66e925245c"
SW1 = "18bd9697-da5c-41f2-8dd5-483315a7c99d"
SW2 = "12adbd8f-7400-4d36-816c-c2b1f0e428b3"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)


def run(cmd, t=25):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(errors="replace").strip()


print("=== proses qemu aktif ===")
print(run("ps -eo pid,args | grep 'qemu-system' | grep -v grep | "
          "sed -E 's/.*(qemu-system-x86_64) -name ([^ ]+).*/\\1 \\2/' | head"))

print("")
print("=== file disk ===")
for label, nid in [("SW1", SW1), ("SW2", SW2)]:
    out = run(f"ls -lh /opt/gns3/projects/{PROJ}/project-files/qemu/{nid}/"
              " 2>/dev/null")
    print(f"--- {label} ---")
    print(out or "(tidak ada)")

sw1_running = run("pgrep -f -- '-name SW1' || true")
print("")
print("SW1 masih jalan?:", sw1_running or "TIDAK (aman dihapus)")
if not sw1_running:
    print("=== hapus disk SW1 ===")
    out = run(f"rm -v /opt/gns3/projects/{PROJ}/project-files/qemu/{SW1}/"
              "hda_disk.qcow2* 2>/dev/null; echo EXIT=$?")
    print(out)
    out = run(f"ls /opt/gns3/projects/{PROJ}/project-files/qemu/{SW1}/"
              " 2>/dev/null || echo '(dir kosong/hilang)'")
    print("sisa isi dir:", out)
else:
    print(">> STOP dulu SW1 di GNS3 GUI, lalu jalankan ulang skrip ini!")
c.close()