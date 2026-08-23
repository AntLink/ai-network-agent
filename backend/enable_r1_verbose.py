"""Enable di R1 - versi hati-hati, output mentah penuh."""
import paramiko
import time

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"
ENABLE_PW = "Admin123!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PW, timeout=20,
               allow_agent=False, look_for_keys=False)
shell = client.invoke_shell(width=200)
time.sleep(2)


def drain(wait=2):
    """Kumpulkan semua output selama `wait` detik."""
    buf = ""
    start = time.time()
    while time.time() - start < wait:
        if shell.recv_ready():
            buf += shell.recv(65535).decode(errors="replace")
            start = time.time()  # reset timer saat masih ada data
        else:
            time.sleep(0.05)
    return buf


print("=== OUTPUT AWAL ===")
print(repr(drain(2)))

print("\n=== KIRIM 'enable' ===")
shell.send("enable\n")
out = drain(3)
print(repr(out))

if "Password" not in out:
    print(">>> TIDAK ADA PROMPT PASSWORD - mungkin langsung masuk priv# ?")

print("\n=== KIRIM PASSWORD ENABLE ===")
shell.send(ENABLE_PW + "\n")
time.sleep(3)
out = drain(3)
print(repr(out))

print("\n=== STATUS ===")
shell.send("\n")
out = drain(2)
print(repr(out))
print("\nPrompt berakhir dengan '#'?" , out.rstrip().endswith("#"))

client.close()