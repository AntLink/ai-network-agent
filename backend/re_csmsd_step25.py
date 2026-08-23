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

LOG = open("re_csmsd_step25_log.txt", "w", encoding="utf-8", errors="replace")


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


def hdr(msg_type, subtype=0, ver=0, bodylen=0):
    return struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, subtype, bodylen)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 25: TYPES 8565 (GREETING) + 8563 (PAN REQ) LIVE TEST")
    out("=" * 70)

    await run(transport, "SANITY", "pidof csmsd.elf || echo dead", timeout=15)

    await run(
        transport,
        "MARK LOG",
        'wc -l < /tmp/csmsd_run.log > /tmp/logmark; cat /tmp/logmark',
        timeout=15,
    )

    tests = [
        ("GREETING type=8565", 8565),
        ("PAN_REQ type=8563", 8563),
        ("GREETING again", 8565),
    ]
    for label, t in tests:
        b = hdr(t)
        esc = "\\x" + "\\x".join(f"{x:02x}" for x in b)
        await run(
            transport,
            f"SEND {label}",
            f"""( printf '{esc}\\n'; sleep 8 ) | nc -w 12 127.0.0.1 3302 2>/dev/null > /tmp/reply.bin &
sleep 11
echo "reply bytes: $(wc -c < /tmp/reply.bin)"
od -A x -t x1z /tmp/reply.bin | head -20
true""".strip(),
            timeout=45,
        )

    await run(
        transport,
        "SERVER LOG since mark",
        """MARK=$(cat /tmp/logmark)
sed -n "${MARK},$ p" /tmp/csmsd_run.log | grep -avE "media r/w|csmsd running" | tail -30
true""",
        timeout=20,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 25 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
