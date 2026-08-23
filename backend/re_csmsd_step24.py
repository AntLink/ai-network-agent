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

LOG = open("re_csmsd_step24_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=40):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


def hdr(msg_type, subtype, ver=0, bodylen=0):
    return struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, subtype, bodylen)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 24: LONG-WINDOW LIVE TESTS")
    out("=" * 70)

    await run(transport, "SANITY", "pidof csmsd.elf || echo dead", timeout=15)

    # mark log position first
    await run(
        transport,
        "MARK LOG",
        'wc -l /tmp/csmsd_run.log | awk \'{print $1}\' > /tmp/logmark; cat /tmp/logmark',
        timeout=15,
    )

    tests = [
        ("GET_CSMS_FAULT (60,5)", 60, 5),
        ("PING (60,3)", 60, 3),
        ("STATUS noop (60,1)", 60, 1),
    ]
    for label, t, s in tests:
        b = hdr(t, s)
        esc = "\\x" + "\\x".join(f"{x:02x}" for x in b)
        # keep stdin open 8s so nc stays alive for late replies
        await run(
            transport,
            f"SEND {label} (window 8s)",
            f"""( printf '{esc}\\n'; sleep 8 ) | nc -w 12 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin &
sleep 11
echo "reply bytes: $(wc -c < /tmp/reply.bin)"
od -A x -t x1z /tmp/reply.bin | head -8
true""".strip(),
            timeout=40,
        )

    # what did the server log since mark?
    await run(
        transport,
        "SERVER LOG since mark",
        """MARK=$(cat /tmp/logmark)
sed -n "${MARK},$ p" /tmp/csmsd_run.log | tail -30
true""",
        timeout=20,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 24 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
