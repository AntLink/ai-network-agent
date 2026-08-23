"""Identifikasi node di konsol 172.22.40.30:5003."""
import socket
import time

HOST, PORT = "172.22.40.30", 5003


def recv_all(s, wait=2.0):
    buf = b""
    start = time.time()
    while time.time() - start < wait:
        try:
            d = s.recv(4096)
            if not d:
                break
            buf += d
            start = time.time()
        except socket.timeout:
            break
    return buf.decode(errors="replace")


def clean(txt):
    # buang escape sequence & backspace noise
    import re
    txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return "\n".join(l.rstrip() for l in txt.splitlines() if l.strip())


def send(s, cmd, wait=2):
    s.send(cmd.encode() + b"\r\n")
    out = recv_all(s, wait)
    print(f"\n>> {cmd}")
    print(clean(out))
    return out


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)

# bangunkan prompt dengan beberapa newline
for _ in range(2):
    s.send(b"\r\n")
    time.sleep(0.5)
print("=== PROMPT AWAL ===")
print(clean(recv_all(s, 2)))

send(s, "show privilege")
send(s, "show version | include Version|Model|uptime", 3)
send(s, "show ip interface brief", 3)

s.close()