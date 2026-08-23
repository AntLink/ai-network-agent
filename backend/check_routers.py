import paramiko
import time

ROUTERS = [
    ("R1", "172.22.45.249"),
    ("R2", "172.22.36.184"),
]
USER = "admin"
PW = "Admin123!"


def check(name, host):
    print(f"===== {name} ({host}) =====")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=USER, password=PW, timeout=20,
                       allow_agent=False, look_for_keys=False)
    except Exception as e:
        print(f"SSH LOGIN GAGAL: {e}")
        return

    shell = client.invoke_shell()
    time.sleep(1)
    while shell.recv_ready():
        shell.recv(65535)

    def send(cmd, timeout=4):
        shell.send(cmd + "\n")
        start = time.time()
        buf = ""
        while time.time() - start < timeout:
            if shell.recv_ready():
                buf += shell.recv(65535).decode(errors="replace")
            time.sleep(0.1)
        return buf

    out = send("show privilege")
    for line in out.splitlines():
        if "privilege level" in line.lower():
            print(f"  {line.strip()}")

    # cek config auth (butuh priv 15; kalau gagal akan ada % error)
    out = send("show running-config | include enable|username|aaa|login local|privilege")
    interesting = [l.strip() for l in out.splitlines()
                   if l.strip() and not l.startswith("show ") and "%" not in l[:2]]
    for line in interesting[:15]:
        print(f"  cfg: {line}")

    client.close()
    print()


for n, h in ROUTERS:
    check(n, h)