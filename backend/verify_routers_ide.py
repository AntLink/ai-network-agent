"""Verifikasi kondisi riil R1/R2 pasca boot IDE."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().>-]+[#>]\s*$")


def recv_all(s, wait=1.5):
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


def send_cmd(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.03)
    s.send(b"\r")


def wait_prompt(s, timeout=45):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = clean(recv_all(s, 1.0))
        buf += c
        lines = [l.strip() for l in buf.splitlines() if l.strip()]
        ll = lines[-1] if lines else ""
        if PROMPT_RE.search(ll):
            return buf, ll
        if ll.endswith(":"):
            return buf, ll
    return buf, ""


for name, port in [("R1", 5006), ("R2", 5008)]:
    print("=" * 22, name, "=" * 22)
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    buf, ll = wait_prompt(s, 20)
    lines = [l.strip() for l in buf.splitlines() if l.strip()]

    # cari prompt terakhir yang bukan 'Password:'
    prompt = ""
    for cand in reversed(lines):
        if PROMPT_RE.search(cand):
            prompt = cand
            break

    if "Password" in buf or (prompt.endswith(">")):
        send_cmd(s, "enable")
        buf, _ = wait_prompt(s, 15)
        if "Password" in buf:
            send_cmd(s, "Admin123!")
            buf, _ = wait_prompt(s, 15)
            if "Bad secrets" in buf:
                print("   [X] password ditolak!")
                s.close()
                continue

    send_cmd(s, "terminal length 0")
    recv_all(s, 4)

    print("--- identitas & intefaces ---")
    send_cmd(s, "show running-config | include hostname|^interface|ip address")
    o, _ = wait_prompt(s, 40)
    keep = []
    for l in o.splitlines():
        ls = l.strip()
        if ls.startswith(("hostname", "interface", "ip address",
                          "encapsulation")):
            keep.append(ls[:80])
    for k_ in keep[:16]:
        print("   ", k_)

    print("--- OSPF ---")
    send_cmd(s, "show ip ospf neighbor")
    o, _ = wait_prompt(s, 30)
    n = 0
    for l in o.splitlines():
        if "FULL" in l:
            n += 1
            print("   ", l.strip()[:75])
    print(f"   neighbor FULL: {n}")

    print("--- ping ke MK ---")
    tgt = "10.255.10.1" if name == "R1" else "10.255.20.1"
    send_cmd(s, f"ping {tgt} repeat 3")
    o, _ = wait_prompt(s, 35)
    m = re.search(r"Success rate is \((\d+)/(\d+)\)", o)
    print(f"   -> {tgt}: {m.group(0) if m else '?'}")

    print("--- startup tersimpan ---")
    send_cmd(s, "show startup-config | include hostname|router ospf")
    o, _ = wait_prompt(s, 40)
    for l in o.splitlines():
        ls = l.strip()
        if ls.startswith(("hostname", "router ospf")):
            print("   ", ls)
    s.close()

print("")
print("=== SELESAI ===")