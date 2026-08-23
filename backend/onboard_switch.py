"""Onboard penuh switch IOSvL2 via konsol telnet GNS3."""
import socket
import time
import re

HOST, PORT = "172.22.40.30", 5003


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


def send(s, cmd, wait=2):
    s.send(cmd.encode() + b"\r\n")
    out = recv_all(s, wait)
    print(f">> {cmd}")
    tail = [l for l in clean(out).splitlines()][-2:]
    for l in tail:
        print(f"   {l}")
    return out


s = socket.create_connection((HOST, PORT), timeout=10)
s.settimeout(1)
recv_all(s, 1.5)

send(s, "enable", 1.5)
send(s, "configure terminal")

print("\n--- konfigurasi dasar ---")
send(s, "hostname SW1")
send(s, "enable secret Admin123!")
send(s, "username admin privilege 15 secret Admin123!")
send(s, "ip domain-name lab.local")

print("\n--- IP manajemen di Vlan1 ---")
send(s, "interface Vlan1")
send(s, "ip address 172.22.38.10 255.255.240.0")
send(s, "no shutdown")
send(s, "exit")

print("\n--- vty: login local + ssh ---")
send(s, "line vty 0 4")
send(s, "login local")
send(s, "privilege level 15")
send(s, "transport input ssh")
send(s, "exit")

send(s, "ip default-gateway 172.22.32.1")
send(s, "end")

print("\n--- generate RSA keys (di EXEC mode) ---")
out = send(s, "crypto key generate rsa modulus 2048", 6)
if "Do you really want" in out or "[confirm]" in out:
    s.send(b"\r\n")
    out += recv_all(s, 5)

print("\n--- aktifkan SSH v2 ---")
send(s, "configure terminal")
send(s, "ip ssh version 2")
send(s, "end")

print("\n--- SIMPAN ---")
out = send(s, "write memory", 6)
print(">>> WRITE MEMORY", "OK" if ("OK" in out or "Building configuration" in out) else "CEK!")

print("\n--- VERIFIKASI ---")
send(s, "show ip ssh")
send(s, "show privilege")
send(s, "show running-config | include hostname|username|ip address|domain|ssh version")

s.close()
print("\n=== ONBOARD SELESAI ===")