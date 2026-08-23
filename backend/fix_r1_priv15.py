"""Fix R1: privilege 15 via login local (no aaa new-model)."""
import paramiko
import time

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PW, timeout=20,
               allow_agent=False, look_for_keys=False)
shell = client.invoke_shell()
time.sleep(1)
while shell.recv_ready():
    shell.recv(65535)

def send(cmd, wait=2):
    shell.send(cmd + "\n")
    time.sleep(wait)
    buf = ""
    while shell.recv_ready():
        buf += shell.recv(65535).decode(errors="replace")
        time.sleep(0.1)
    tail = [l for l in buf.splitlines() if l.strip()][-3:]
    print(f">> {cmd}")
    for l in tail:
        print(f"   {l.strip()}")
    return buf

send("enable", 1)
send("Admin123!", 2)
send("configure terminal")
# inti: user priv 15 + enable secret
send("username admin privilege 15 secret Admin123!")
send("enable secret Admin123!")
# hapus aaa sisa percobaan lama (aman, tidak memutus sesi)
send("no aaa new-model")
send("line vty 0 4")
send("login local")
send("privilege level 15")
send("transport input ssh")
send("exit")
send("end")
# simpan SEGERA
send("write memory", 4)
# verifikasi
out = send("show privilege", 2)
if "15" in out:
    print("\n=== R1 SEKARANG PRIVILEGE 15 ===")
else:
    print("\n=== MASIH BELUM PRIV 15 ===")

client.close()