"""Reload SW1 dan tangkap log boot lengkap (diagnosis flash0)."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=3.0):
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


def send(s, cmd, wait=4):
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")
    return clean(recv_all(s, wait))


s = socket.create_connection((VM, 5002), timeout=10)
s.settimeout(0.5)
recv_all(s, 4)
send(s, "")
o = send(s, "enable", 4)
if "Password" in o:
    send(s, "Admin123!", 5)

print(">> memicu reload...")
send(s, "reload", 6)
# jawab konfirmasi
for _ in range(3):
    o = recv_all(s, 4)
    print("   konfirmasi:", [l.strip() for l in o.splitlines()
                             if l.strip()][-1:])
    if "[confirm]" in o or "confirm" in o.lower():
        send(s, "", 3)
        break
    send(s, "\r" if "Proceed" in o else "", 2)
else:
    pass

print(">> menunggu proses boot (maks 8 menit)...")
log = ""
t0 = time.time()
booted = False
while time.time() - t0 < 480:
    chunk = clean(recv_all(s, 2))
    if chunk:
        log += chunk
        if "Press RETURN to get started" in log:
            booted = True
            break
        # tampilkan progress tiap milestone penting
        for marker in ["Booting", "Linux version", "Mount",
                       "%SIGNATURE", "ATA-", "flash", "IOSv Software"]:
            if marker in chunk and marker not in log[:len(log)-len(chunk)]:
                line = [l.strip() for l in chunk.splitlines()
                        if marker in l][:1]
                if line:
                    print("   ...", line[0][:110])

print(">> boot selesai:", booted)
send(s, "", 5)
o = send(s, "enable", 6)
if "Password" in o:
    send(s, "Admin123!", 6)
send(s, "terminal length 0", 5)
o = send(s, "show file systems", 20)
print("=== show file systems ===")
for l in o.splitlines():
    ls = l.strip()
    if ls and not ls.startswith(("show", "SW1")):
        print("   ", l.rstrip()[:120])
o = send(s, "show logging | include SIGNATURE|ATA|flash|Mount", 30)
print("=== logging terkait ===")
for l in o.splitlines():
    ls = l.strip()
    if any(k in ls for k in ("SIGNATURE", "ATA", "flash", "Mount")) \
            and not ls.startswith("show"):
        print("   ", ls[:130])
with open(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\sw1_boot.log",
          "w", encoding="utf-8") as f:
    f.write(log)
print("(log penuh disimpan ke sw1_boot.log)")
s.close()