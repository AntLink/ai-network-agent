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

LOG = open("re_csmsd_step22_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=30):
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
    out("  STEP 22: LIVE PING TEST (type=60, subtype=3)")
    out("=" * 70)

    # sanity: service up?
    await run(transport, "SANITY", "pidof csmsd.elf || echo dead", timeout=15)

    for label, t, s in [("PING (60,3)", 60, 3), ("NOOP (60,1)", 60, 1), ("CTRL (60,5)", 60, 5)]:
        b = hdr(t, s)
        esc = "\\x" + "\\x".join(f"{x:02x}" for x in b)
        await run(
            transport,
            f"SEND {label}",
            f"""printf '{esc}\\n' | timeout 4 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1 | head -8
true""",
            timeout=20,
        )

    # check server log for PING_SERVER_RMS
    await run(
        transport,
        "SERVER LOG: ping received?",
        """grep -a "PING" /tmp/csmsd_run.log | tail -5
grep -aiE "ping|equipcontrol" /tmp/csmsd_run.log | tail -10
true""",
        timeout=20,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead; netstat -tlnp 2>/dev/null | grep -c csmsd; true", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 22 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
