import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

LOG = open("re_csmsd_step13_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=25):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except asyncio.TimeoutError:
        out(f"(TIMEOUT after {timeout}s)")
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


def hdr(msg_type, ver=0, status=0, bodylen=0):
    import struct
    return struct.pack("<IIHBBII", 0, 0, msg_type, ver, 0, status, bodylen)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 13: MULTI-MESSAGE CONNECTION TEST + WIDE TYPE SWEEP + RT PORT")
    out("=" * 70)

    # ---- Test: does server handle multiple msgs per connection? --------------
    hx1 = hdr(1).hex()
    hx27 = hdr(27).hex()
    e1 = "\\x" + "\\x".join(hx1[i:i + 2] for i in range(0, len(hx1), 2))
    e2 = "\\x" + "\\x".join(hx27[i:i + 2] for i in range(0, len(hx27), 2))
    await run(
        transport,
        "MULTI-MSG: two messages one connection",
        f"""printf '{e1}\\n{e2}\\n' | timeout 4 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1
true""",
        timeout=20,
    )

    # ---- Wide sweep using piped python-free approach: batch via xargs --------
    # Build one big printf containing messages for types 0..199 each followed by \n,
    # send over ONE connection, capture all responses.
    blob_parts = []
    for t in range(0, 200):
        h = hdr(t).hex()
        blob_parts.append("\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2)) + "\\n")
    blob = "".join(blob_parts)

    await run(
        transport,
        "SWEEP 3302: types 0..199 single connection",
        f"""printf '{blob}' | timeout 8 nc 127.0.0.1 3302 2>/dev/null | od -A d -t x1 > /tmp/sweep.out
wc -c /tmp/sweep.out
head -50 /tmp/sweep.out
true""",
        timeout=40,
    )

    # ---- Port 3307 with 12-byte RealtimeNet-style header ----------------------
    # CRealtimeNet: HeaderSize=12, BodySize=u32@offset8, delimiter \n
    rt = struct.pack("<IIII", 0, 0, 0, 0).hex()
    ert = "\\x" + "\\x".join(rt[i:i + 2] for i in range(0, len(rt), 2))
    await run(
        transport,
        "PORT 3307: 12-byte realtime header",
        f"""printf '{ert}\\n' | timeout 4 nc 127.0.0.1 3307 2>/dev/null | od -A x -t x1 | head -8
true""",
        timeout=20,
    )

    # Also newline-only probe on 3307 (RDS-style?)
    await run(
        transport,
        "PORT 3307: bare newline",
        """printf '\\n' | timeout 4 nc 127.0.0.1 3307 2>/dev/null | od -A x -t x1 | head -8
true""",
        timeout=20,
    )

    # ---- health -----------------------------------------------------------------
    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 13 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
