"""Perbaiki NV storage SW1/SW2: cek flash, hapus vlan.dat rusak, uji tulis."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().-]+[#>]\s*$")


def recv_all(s, wait=2.0):
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


def wait_prompt(s, timeout=90):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        chunk = clean(recv_all(s, 1.5))
        if chunk:
            buf += chunk
            lines = [l.strip() for l in buf.splitlines() if l.strip()]
            if lines and PROMPT_RE.search(lines[-1]):
                return buf, lines[-1]
        else:
            s.send(b"\r")
    return buf, ""


def cmd(s, c, timeout=120, show=True):
    s.send(c.encode())
    time.sleep(0.03)
    s.send(b"\r")
    out, _ = wait_prompt(s, timeout)
    if show:
        print(">>", c)
        for l in out.splitlines():
            ls = l.strip()
            if ls and not ls.startswith(("show", "SW", "dir", "delete",
                                         "copy", "vlan", "end")):
                print("   ", ls[:130])
    return out


def connect(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 4)
    s.send(b"\r")
    wait_prompt(s, 30)
    s.send(b"enable\r")
    out, _ = wait_prompt(s, 15)
    if "Password" in out:
        s.send(b"Admin123!\r")
        wait_prompt(s, 15)
    cmd(s, "terminal length 0")
    return s


for name, port in [("SW1", 5002), ("SW2", 5004)]:
    print("=" * 20, name, "=" * 20)
    s = connect(port)

    print("--- isi flash ---")
    cmd(s, "dir flash:")

    print("--- hapus vlan.dat ---")
    o = cmd(s, "delete flash:vlan.dat")
    if "[confirm]" in o or "Delete filename" in o:
        s.send(b"\r")
        recv_all(s, 3)
        s.send(b"\r")
        recv_all(s, 3)

    print("--- uji tulis flash ---")
    cmd(s, "configure terminal")
    cmd(s, "vlan 10")
    cmd(s, "name USERS")
    cmd(s, "exit")
    cmd(s, "vlan 20")
    cmd(s, "name SERVERS")
    cmd(s, "end")
    cmd(s, "write memory", 180)
    o = cmd(s, "show vlan brief", 150)
    ok = [l.strip() for l in o.splitlines()[:8]]
    for l in ok:
        print("   >", l[:110])
    m = re.search(r"^10\s+\S+", "\n".join(o.splitlines()), re.M)
    print("   RESULT vlan10:", bool(m))
    s.close()

print("")
print("=== SELESAI ===")