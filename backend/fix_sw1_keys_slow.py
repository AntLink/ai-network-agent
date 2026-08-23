"""Kirim perintah ke konsol SW1 secara per-karakter (anti hilang huruf)."""
import socket
import time
import re

HOST, PORT = "172.22.40.30", 5003
CHAR_DELAY = 0.03


def recv_all(s, wait=2.5):
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
    txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", txt)
    txt = re.sub(r"[\x00-\x08\x0b-\x1f]", "", txt)
    return "\n".join(l.rstrip() for l in txt.splitlines() if l.strip())


def slow_send(s, cmd, wait=3):
    """Ketik per karakter lalu Enter."""
    for ch in cmd:
        s.send(ch.encode())
        time.sleep(CHAR_DELAY)
    s.send(b"\r")
    out = recv_all(s, wait)
    print(f">> {cmd}")
    print(clean(out))
    return out


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1)

slow_send(s, "enable", 1.5)

print("\n=== GENERATE RSA KEYS ===")
out = slow_send(s, "crypto key generate rsa modulus 2048", 8)
if "[yes/no]" in out or "confirm" in out.lower() or "Do you really" in out:
    s.send(b"\r")
    print(clean(recv_all(s, 8)))
elif "Invalid" in out:
    # fallback sintaks alternatif
    print("\n--- coba sintaks general-keys ---")
    out = slow_send(s, "crypto key generate rsa general-keys modulus 2048", 8)
    if "[yes/no]" in out or "confirm" in out.lower():
        s.send(b"\r")
        print(clean(recv_all(s, 8)))

print("\n=== VERIFIKASI KEYS ===")
slow_send(s, "show crypto key mypubkey rsa", 3)
slow_send(s, "show ip ssh | include SSH", 3)

print("\n=== SIMPAN ===")
out = slow_send(s, "write memory", 5)
print("WRITE MEMORY:", "OK" if "OK" in out or "Building" in out else "?")

s.close()