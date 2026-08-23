import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

LOG = open("re_csmsd_step26_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=45):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


def hdr(msg_type, subtype=0, ver=0, bodylen=0):
    return struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, subtype, bodylen)


def esc(b):
    h = b.hex()
    return "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 26: SINGLE-CONNECTION SEQUENCE GREETING -> PAN")
    out("=" * 70)

    await run(transport, "SANITY", "pidof csmsd.elf || echo dead", timeout=15)

    greet0 = hdr(8565)                                   # tanpa body
    greet36 = hdr(8565, bodylen=36) + b"\x00" * 36       # body 36 zero
    pan36 = hdr(8563, bodylen=36) + b"\x00" * 36
    pan0 = hdr(8563)

    experiments = [
        ("A: greet(no body) + pan(no body)", greet0, pan0),
        ("B: greet(36B zeros) + pan(36B zeros)", greet36, pan36),
        ("C: greet(36B zeros) only", greet36, None),
    ]

    for label, first, second in experiments:
        msgs = esc(first) + "\\n"
        if second:
            msgs += esc(second) + "\\n"
        await run(
            transport,
            f"{label} (one connection, 12s)",
            f"""rm -f /tmp/reply.bin
( printf '{msgs}'; sleep 12 ) | nc -w 15 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin &
sleep 15
echo "reply bytes: $(wc -c < /tmp/reply.bin)"
od -A x -t x1z /tmp/reply.bin | head -24
true""".strip(),
            timeout=50,
        )

    await run(
        transport,
        "SERVER LOG grep GREETING/PAN",
        'grep -aE "GREETING|MEASUREMENT|PanReq|panorama" /tmp/csmsd_run.log | tail -10; true',
        timeout=20,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 26 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
