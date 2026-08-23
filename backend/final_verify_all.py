"""Verifikasi final menyeluruh pasca rebuild socket (tunggu boot dulu)."""
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


def wait_prompt(s, timeout=60):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = clean(recv_all(s, 1.0))
        buf += c
        ll = buf.strip().splitlines()[-1].strip() if buf.strip() else ""
        if PROMPT_RE.search(ll):
            return buf, ll
    return buf, ""


def send_cmd(s, c, slow=False):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.03 if slow else 0.02)
    s.send(b"\r")


def session(port, name_hint="#"):
    """Koneksi konsol; tunggu boot bila perlu; enable bila perlu."""
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    buf, ll = wait_prompt(s, 300)
    last = ll or ""
    if "#" in last:
        return s
    if ">" in last:
        send_cmd(s, "enable")
        buf, ll = wait_prompt(s, 20)
        if "Password" in buf:
            send_cmd(s, "Admin123!")
            wait_prompt(s, 20)
        return s
    # mungkin masih booting / kosong: coba lagi
    send_cmd(s, "")
    buf, ll = wait_prompt(s, 120)
    if "Password" in buf:
        send_cmd(s, "Admin123!")
        wait_prompt(s, 15)
    elif ">" in ll:
        send_cmd(s, "enable")
        buf2, ll2 = wait_prompt(s, 20)
        if "Password" in buf2:
            send_cmd(s, "Admin123!")
            wait_prompt(s, 20)
    return s


print("[i] menunggu semua device selesai boot...")
time.sleep(150)

results = []


def check(label, fn):
    try:
        r = fn()
        results.append((label, r))
        print(f"   {label}: {r}")
    except Exception as e:
        results.append((label, f"ERR {type(e).__name__}"))
        print(f"   {label}: ERR {e}")


# --- counter SW1 Gi0/0 harus bergerak ---
def sw_counter():
    s = session(5002)
    send_cmd(s, "show interfaces GigabitEthernet0/0")
    o = wait_prompt(s, 25)[0].replace("\n", " ")
    m = re.search(r"(\d+) packets input", o)
    v = int(m.group(1)) if m else -1
    time.sleep(8)
    send_cmd(s, "")
    o = clean(recv_all(s, 5))
    send_cmd(s, "show interfaces GigabitEthernet0/0")
    o = wait_prompt(s, 25)[0].replace("\n", " ")
    m = re.search(r"(\d+) packets input", o)
    v2 = int(m.group(1)) if m else -1
    s.close()
    return f"in {v} -> {v2} ({'ALIRAN OK' if v2 > v else 'BEKU'})"


check("SW1 Gi0/0 rx", sw_counter)


# --- OSPF R1 ---
def ospf_r1():
    s = session(5006)
    send_cmd(s, "show ip ospf neighbor", True)
    o = wait_prompt(s, 20)[0]
    fulls = len([l for l in o.splitlines() if "FULL" in l])
    send_cmd(s, "show ip route ospf | include ^O", True)
    o = wait_prompt(s, 15)[0]
    routes = len([l for l in o.splitlines()
                  if l.strip().startswith("O ")])
    s.close()
    return f"{fulls} neighbor FULL, {routes} route OSPF"


check("R1 OSPF", ospf_r1)

# --- ping antar PC ---
PCP = {"A": 5010, "B": 5014}
TESTS = [
    (5010, "192.168.10.1", "PC-A1->GW"),
    (5010, "192.168.30.10", "PC-A1->PC-B1"),
    (5010, "192.168.100.10", "PC-A1->PC-M"),
    (5016, "192.168.20.10", "PC-B2->PC-A2"),
]


def pc_ping(port, target):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 2)
    send_cmd(s, "", slow=True)
    recv_all(s, 1.5)
    send_cmd(s, f"ping {target}", slow=True)
    out = ""
    t0 = time.time()
    while time.time() - t0 < 30:
        out += clean(recv_all(s, 1.0))
        if re.search(r"\*\*\*|not reachable|100\.00%", out) and len(out) > len(target) + 40:
            pass
        if out.count("\n") >= 3 and ("bytes from" in out or "100.00%" in out or "not reachable" in out):
            if "bytes from" in out:
                n = len(re.findall(r"bytes from", out))
                if n >= 4:
                    break
    replies = len(re.findall(r"bytes from", out))
    s.close()
    return f"{replies}/5"


for port, tgt, label in TESTS:
    check(label, lambda p=port, t=tgt: pc_ping(p, t))

print("")
ok = sum(1 for _, r in results if "OK" in str(r) or "/5" in str(r)
         and not str(r).startswith("0/5"))
print("=== RINGKASAN ===")
for label, r in results:
    print(f"   {label:<18} : {r}")