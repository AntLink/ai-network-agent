"""Periksa R1/R2: tanda boot baru, error signature, umur disk."""
import re
import socket
import time
import paramiko

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=5.0):
    buf = b""
    start = time.time()
    while time.time() - start < wait:
        try:
            d = s.recv(65535)
            if not d:
                break
            buf += d
            start = time.time()
        except socket.timeout:
            break
    return buf.decode(errors="replace")


def clean(txt):
    txt = re.sub(ESC + r"\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return txt


for name, port in [("R1", 5006), ("R2", 5008)]:
    print("==========", name, "==========")
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    s.send(b"\r")
    buf = clean(recv_all(s, 8))
    lines = [l.strip() for l in buf.splitlines() if l.strip()]
    print("prompt:", lines[-1] if lines else "?")
    print("signature FAILED:", "ADA!" if "SIGNATURE_FAILED" in buf
          or "SIGNATURE FAILED" in buf else "tidak terlihat")
    print("ATA error:", "ADA!" if "ATA-3-DEV_ERROR" in buf else "tidak")
    s.close()

print("")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(VM, username="gns3", password="gns3", timeout=10,
          allow_agent=False, look_for_keys=False)


def run(cmd, t=25):
    i, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode(errors="replace").strip()


P = "/opt/gns3/projects/a6967457-f60e-4752-be8f-6b66e925245c/" \
    "project-files/qemu"
out = run(f"ls -lh --time-style=+%H:%M {P}/*/hda_disk.qcow2 "
          f"| sed 's|.*/qemu/||'")
print("=== umur disk semua node ===")
print(out)
print("")
print("=== proses qemu ===")
print(run("ps -eo args | grep qemu-system | grep -v grep | "
          "grep -oE '\\-name [A-Za-z0-9]+'"))
c.close()