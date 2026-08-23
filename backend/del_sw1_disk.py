"""Hapus disk SW1 (node sudah distop)."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("172.22.37.68", username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)


def run(cmd, t=25):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(errors="replace").strip()


P = ("/opt/gns3/projects/a6967457-f60e-4752-be8f-6b66e925245c/"
     "project-files/qemu/18bd9697-da5c-41f2-8dd5-483315a7c99d")
print("sebelum :", run("ls " + P))
print("hapus   :", run("rm -v " + P + "/hda_disk.qcow2*"))
print("sesudah :", run("ls " + P))
q = run("pgrep -fc 'name SW1' || true")
print("proses SW1:", q if q else "TIDAK ADA")
c.close()