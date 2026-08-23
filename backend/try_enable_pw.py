"""Try enable passwords on R1."""
import paramiko
import time

HOST = "172.22.45.249"
USER = "admin"
CANDIDATES = [
    "815m1ll4h",   # password umum proyek ini
    "cisco",
    "cisco123",
    "class",
    "admin",
    "Cisco123!",
    "password",
    "cisco1",
]

for pw in CANDIDATES:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password="Admin123!", timeout=15,
                       allow_agent=False, look_for_keys=False)
    except Exception as e:
        print(f"[!] SSH login gagal: {e}")
        break

    shell = client.invoke_shell()
    time.sleep(1)
    while shell.recv_ready():
        shell.recv(65535)

    shell.send("enable\n")
    time.sleep(1)
    while shell.recv_ready():
        shell.recv(65535)

    shell.send(pw + "\n")
    time.sleep(2)
    buf = ""
    while shell.recv_ready():
        buf += shell.recv(65535).decode(errors="replace")
        time.sleep(0.1)

    ok = buf.rstrip().endswith("#") and "Error" not in buf
    print(f"{'[OK]' if ok else '[--]'} enable dengan '{pw}' -> {buf.strip().splitlines()[-1] if buf.strip() else '(kosong)'}")

    if ok:
        # verifikasi privilege
        shell.send("show privilege\n")
        time.sleep(1.5)
        out = ""
        while shell.recv_ready():
            out += shell.recv(65535).decode(errors="replace")
            time.sleep(0.1)
        for line in out.splitlines():
            if "privilege level" in line.lower():
                print("     ", line.strip())
        client.close()
        break
    client.close()