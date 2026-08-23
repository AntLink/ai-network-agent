import asyncio
import re

import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"

PROMPT_RE = re.compile(r"(?m)^[^\r\n]+(?:\(config[^)]*\))?[#>]\s*$")
CONFIRM_RE = re.compile(r"(\?|\[confirm\])\s*$")


async def read_chunk(reader, max_wait=6.0):
    buf = ""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < max_wait:
        try:
            piece = await asyncio.wait_for(reader.read(4096), timeout=0.3)
        except asyncio.TimeoutError:
            break
        if not piece:
            break
        buf += piece
        if PROMPT_RE.search(buf) or CONFIRM_RE.search(buf.rstrip()):
            break
    return buf


async def send_command(proc, command, max_wait=15.0, confirms=4):
    """Kirim perintah, jawab semua prompt konfirmasi sampai prompt CLI."""
    proc.stdin.write(command + "\n")
    full = ""
    for _ in range(confirms + 1):
        out = await read_chunk(proc.stdout, max_wait)
        full += out
        if CONFIRM_RE.search(out.rstrip()) and not PROMPT_RE.search(out.rstrip()):
            proc.stdin.write("\n")  # terima default
            continue
        if PROMPT_RE.search(full):
            break
    return full


async def main():
    conn = await asyncssh.connect(HOST, username=USER, password=PW, known_hosts=None)
    proc = await conn.create_process(term_type="dumb", term_size=(511, 24))
    await read_chunk(proc.stdout)

    print("== terminal length 0 ==")
    out = await send_command(proc, "terminal length 0")
    print("(ok)" if PROMPT_RE.search(out) else "(?)")

    print("== copy running-config flash0:pretxn.cfg ==")
    out = await send_command(proc, "copy running-config flash0:pretxn.cfg", max_wait=20.0)
    tail = [l.strip() for l in out.replace("\r", "").splitlines() if l.strip()]
    print("tail:", tail[-4:])

    print("== dir flash0: | include pretxn ==")
    out = await send_command(proc, "dir flash0: | include pretxn", max_wait=10.0)
    hits = [l.strip() for l in out.splitlines() if "pretxn" in l.lower()]
    print("hits:", hits if hits else "TIDAK ADA")

    print("== configure replace flash0:pretxn.cfg force ==")
    out = await send_command(proc, "configure replace flash0:pretxn.cfg force", max_wait=40.0)
    lines = [l.strip() for l in out.replace("\r", "").splitlines() if l.strip()]
    print("out:", lines[:8])

    print("== delete /force flash0:pretxn.cfg ==")
    out = await send_command(proc, "delete /force flash0:pretxn.cfg", max_wait=10.0)
    print("done" if out else "(kosong)")

    proc.stdin.write("exit\n")
    try:
        await asyncio.wait_for(proc.wait(), timeout=3)
    except Exception:
        pass
    conn.close()


asyncio.run(main())
