import asyncio
import socket
import time

import asyncssh

HOST = "172.22.45.249"
USER = "admin"
PW = "Admin123!"
PROMPT_RE = None  # filled after we see the banner


def ms(x: float) -> str:
    return f"{x * 1000:.0f} ms"


def bench_tcp_banner() -> float:
    s0 = time.perf_counter()
    c = socket.create_connection((HOST, 22), timeout=10)
    c.recv(256)
    c.close()
    return time.perf_counter() - s0


async def drain_until_prompt(reader, max_wait=6.0):
    """Read until output ends with a CLI prompt (# or >)."""
    buf = ""
    s0 = time.perf_counter()
    while time.perf_counter() - s0 < max_wait:
        try:
            piece = await asyncio.wait_for(reader.read(4096), timeout=0.25)
        except asyncio.TimeoutError:
            if buf.rstrip().endswith(("#", ">")):
                break
            continue
        if not piece:
            break
        buf += piece
        if buf.rstrip().endswith(("#", ">")):
            break
    return buf, time.perf_counter() - s0


async def main():
    samples_tcp = [bench_tcp_banner() for _ in range(3)]
    print(f"TCP+banner x3   : {', '.join(ms(s) for s in samples_tcp)}")

    for i in range(3):
        s0 = time.perf_counter()
        conn = await asyncssh.connect(
            HOST, username=USER, password=PW,
            known_hosts=None, connect_timeout=15,
        )
        t_conn = time.perf_counter() - s0

        s1 = time.perf_counter()
        res = await conn.run("show clock", check=False)
        t_exec = time.perf_counter() - s1
        out_len = len(res.stdout or "")

        s2 = time.perf_counter()
        conn.close()
        await conn.wait_closed()
        t_close = time.perf_counter() - s2

        print(
            f"run#{i + 1}: connect={ms(t_conn)}  exec(show clock)={ms(t_exec)} "
            f"({out_len}B)  close={ms(t_close)}"
        )

    print("--- interaktif (create_process) ---")
    conn = await asyncssh.connect(
        HOST, username=USER, password=PW,
        known_hosts=None, connect_timeout=15,
    )
    s0 = time.perf_counter()
    proc = await conn.create_process(term_type="dumb", term_size=(511, 24))
    buf, t_first = await drain_until_prompt(proc.stdout)
    print(f"open+banner     : {ms(time.perf_counter() - s0)} (prompt after {ms(t_first)})")

    for cmd in ["terminal length 0", "show clock", "show ip interface brief"]:
        s1 = time.perf_counter()
        proc.stdin.write(cmd + "\n")
        out, dt = await drain_until_prompt(proc.stdout)
        lines = len(out.splitlines())
        print(f"cmd '{cmd[:26]:<28}': {ms(dt)} ({lines} lines)")

    s2 = time.perf_counter()
    proc.stdin.write("exit\n")
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except Exception:
        pass
    print(f"exit            : {ms(time.perf_counter() - s2)}")
    conn.close()


asyncio.run(main())
