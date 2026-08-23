"""Cek status boot SW1 & SW2 pasca perubahan disk ke SATA."""
import re
import socket
import time

VM = "172.22.37.68"
ESC = chr(27)


def recv_all(s, wait=6.0):
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


for name, port in [("SW1", 5002), ("SW2", 5004)]:
    print("==========", name, "==========")
    s = socket.create_connection((VM, port), timeout=10)
    s.settimeout(1)
    buf = ""
    t0 = time.time()
    while time.time() - t0 < 40:
        buf += clean(recv_all(s, 4))
        lines = [l.strip() for l in buf.splitlines() if l.strip()]
        if lines and re.search(r"(Switch|SW1|SW2)[>#]$", lines[-1]):
            break
        if "SIGNATURE_FAILED" in buf:
            print("   !! MASIH ADA SIGNATURE_FAILED")
        if "[yes/no]" in buf[-200:]:
            s.send(b"no\r")
            continue
        s.send(b"\r")
    lines = [l.strip() for l in buf.splitlines() if l.strip()]
    print("prompt:", lines[-1] if lines else "(kosong)")
    sig_fail = "SIGNATURE FAILED" in buf or "SIGNATURE_FAILED" in buf
    ata_err = "ATA-3-DEV_ERROR" in buf
    print("signature gagal:", "YA" if sig_fail else "tidak terlihat",
          "| ATA error:", "ADA" if ata_err else "tidak")

    # cek cepat hostname via console
    def slow(cmd, wait=8):
        for ch in cmd:
            s.send(ch.encode())
            time.sleep(0.03)
        s.send(b"\r")
        return clean(recv_all(s, wait))

    slow("", 2)
    out = slow("enable", 8)
    out = slow("terminal length 0", 10)
    out = slow("show running-config | include hostname", 20)
    hl = [l.strip() for l in out.splitlines() if "hostname" in l]
    print("running hostname:", hl[-1] if hl else "?")
    out = slow("show startup-config | include hostname", 25)
    hl = [l.strip() for l in out.splitlines() if "hostname" in l]
    print("startup  hostname:", hl[-1] if hl else "(kosong)")
    s.close()
    print()