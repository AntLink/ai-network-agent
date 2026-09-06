import subprocess

proc = subprocess.Popen(
    [r"C:\Program Files\PuTTY\plink.exe", "-batch", "-telnet", "-P", "5019", "172.21.0.2"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
try:
    out, err = proc.communicate(b"\r\necho READY\r\n", timeout=8)
except subprocess.TimeoutExpired:
    proc.kill()
    out, err = proc.communicate()
print(out.decode("utf-8", errors="replace")[-8000:])
if err:
    print(err.decode("utf-8", errors="replace")[-1000:])
