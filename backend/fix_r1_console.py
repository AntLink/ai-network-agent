"""R1 fix lengkap via konsol telnet GNS3 - priv 15 permanen."""
import socket
import time

HOST, PORT = "172.22.40.30", 5005


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


def send(s, cmd, wait=1.5):
    s.send(cmd.encode() + b"\r\n")
    out = recv_all(s, wait)
    print(f">> {cmd}")
    return out


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)

# pastikan di privileged mode
recv_all(s, 1.5)
send(s, "enable", 2)
send(s, "configure terminal")

# konfigurasi inti (ala R2, TANPA aaa new-model)
send(s, "username admin privilege 15 secret Admin123!")
send(s, "enable secret Admin123!")
send(s, "no aaa new-model")
send(s, "line vty 0 4")
send(s, "login local")
send(s, "privilege level 15")
send(s, "transport input ssh")
send(s, "exit")
send(s, "end")

print("\n=== SIMPAN ===")
out = send(s, "write memory", 6)
if "OK" in out or "Building configuration" in out:
    print(">>> WRITE MEMORY OK")
else:
    print(">>> PERIKSA OUTPUT:", repr(out))

print("\n=== VERIFIKASI DI KONSOL ===")
send(s, "show privilege")
send(s, "show running-config | include username|aaa|login local|privilege|enable secret")

s.close()
print("\n=== SELESAI - lanjut verifikasi SSH ===")