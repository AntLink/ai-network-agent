import subprocess
import time

commands = [
    "ip link set eth0 up",
    "ip addr flush dev eth0",
    "ip addr add 192.168.10.20/24 dev eth0",
    "ping -c 2 -W 2 192.168.10.1",
    "ssh-keyscan -T 5 192.168.10.1",
]
proc = subprocess.Popen(
    [r"C:\Program Files\PuTTY\plink.exe", "-batch", "-telnet", "-P", "5019", "172.21.0.2"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
try:
    proc.stdin.write(b"root\r\n")
    proc.stdin.flush()
    time.sleep(1)
    proc.stdin.write(b"\r\n")
    proc.stdin.flush()
    time.sleep(1)
    for command in commands:
        proc.stdin.write((command + "\r\n").encode())
        proc.stdin.flush()
        time.sleep(2)
    proc.stdin.close()
    out = proc.stdout.read()
    err = proc.stderr.read()
except Exception:
    proc.kill()
    out, err = proc.communicate()
print(out.decode("utf-8", errors="replace")[-12000:])
if err:
    print(err.decode("utf-8", errors="replace")[-2000:])
