"""Verifikasi SSH semua perangkat Cisco setelah Phase 1."""
import paramiko
import time

DEVICES = [
    ("R1", "172.22.45.249"),
    ("R2", "172.22.36.184"),
    ("SW1", "172.22.38.10"),
    ("SW2", "172.22.39.10"),
]

for name, ip in DEVICES:
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(ip, username="admin", password="Admin123!", timeout=12,
                  allow_agent=False, look_for_keys=False)
        sh = c.invoke_shell()
        time.sleep(1.5)
        while sh.recv_ready():
            sh.recv(65535)
        sh.send("show privilege\n")
        time.sleep(2)
        out = ""
        while sh.recv_ready():
            out += sh.recv(65535).decode(errors="replace")
            time.sleep(0.2)
        lvl = next((l.strip() for l in out.splitlines()
                    if "privilege level" in l.lower()), "?")
        prompt = out.strip().splitlines()[-1] if out.strip() else "?"
        print(f"{name:<4} {ip:<16} {lvl:<35} prompt={prompt}")
        c.close()
    except Exception as e:
        print(f"{name:<4} {ip:<16} GAGAL: {type(e).__name__}: {e}")