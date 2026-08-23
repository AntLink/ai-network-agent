"""Counter mentah Gi0/0 SW1 vs Gi0/1 R1 (tanpa filter pipe)."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)
PROMPT_RE = re.compile(r"[A-Za-z0-9().>-]+[#>]\s*$")


def recv_all(s, wait=2.5):
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


def wait_prompt(s, timeout=45):
    buf = ""
    t0 = time.time()
    while time.time() - t0 < timeout:
        c = clean(recv_all(s, 1.0))
        buf += c
        ll = buf.strip().splitlines()[-1].strip() if buf.strip() else ""
        if PROMPT_RE.search(ll):
            return buf
    return buf


def send_cmd(s, c):
    for ch in c:
        s.send(ch.encode())
        time.sleep(0.02)
    s.send(b"\r")


def session(port):
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(0.5)
    recv_all(s, 3)
    send_cmd(s, "")
    wait_prompt(s, 30)
    o = wait_prompt(s, 3)
    last = o.strip().splitlines()[-1] if o.strip() else ""
    if not last.endswith("#"):
        send_cmd(s, "enable")
        o = wait_prompt(s, 15)
        if "Password" in o:
            send_cmd(s, "Admin123!")
            wait_prompt(s, 15)
    send_cmd(s, "terminal length 0")
    wait_prompt(s, 8)
    return s


def counters(s, intf):
    send_cmd(s, f"show interfaces {intf}")
    o = wait_prompt(s, 25)
    inp = re.search(r"(\d+) packets input", o.replace("\n", " "))
    outp = re.search(r"(\d+) packets output", o.replace("\n", " "))
    return (int(inp.group(1)) if inp else -1,
            int(outp.group(1)) if outp else -1)


print("=== SW1 Gi0/0 ===")
s = session(5002)
i1, o1 = counters(s, "GigabitEthernet0/0")
print(f"   t0: in={i1} out={o1}")
time.sleep(15)
i2, o2 = counters(s, "GigabitEthernet0/0")
print(f"   t15: in={i2} out={o2}  (delta in={i2-i1}, out={o2-o1})")
s.close()

print("")
print("=== R1 Gi0/1 ===")
s = session(5006)
r1, t1 = counters(s, "GigabitEthernet0/1")
print(f"   t0: in={r1} out={t1}")
time.sleep(15)
r2, t2 = counters(s, "GigabitEthernet0/1")
print(f"   t15: in={r2} out={t2}  (delta in={r2-r1}, out={t2-t1})")
s.close()