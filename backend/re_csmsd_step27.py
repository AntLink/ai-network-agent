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

LOG = open("re_csmsd_step27_log.txt", "w", encoding="utf-8", errors="replace")


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


def hdr(msg_type, subtype=0, ver=0, bodylen=0, marker=0):
    return struct.pack("<IIHBBII", marker, 0, msg_type, ver, 0, subtype, bodylen)


def esc(b):
    h = b.hex()
    return "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 27: CMDVER SWEEP FOR GREETING(8565) / PAN(8563)")
    out("=" * 70)

    await run(transport, "SANITY", "pidof csmsd.elf || echo dead", timeout=15)

    # greeting with cmdVer 1..8, marker = 100+ver, 36-byte zero body
    lines = ["rm -f /tmp/rv_*.txt"]
    for v in range(1, 9):
        b = hdr(8565, ver=v, bodylen=36, marker=100 + v)
        lines.append(
            f"( printf '{esc(b)}\\n'; sleep 5 ) | nc -w 8 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n' > /tmp/rv_g{v}.txt &"
        )
        if v % 4 == 0:
            lines.append("wait")
            lines.append("sleep 1")
    lines.append("wait")
    lines.append("for f in $(ls -v /tmp/rv_g*.txt); do echo \"$f: $(cat $f)\"; done")
    await run(transport, "GREETING ver sweep 1-8", "\n".join(lines) + "\ntrue", timeout=90)

    lines = ["rm -f /tmp/rp_*.txt"]
    for v in range(1, 9):
        b = hdr(8563, ver=v, bodylen=36, marker=200 + v)
        lines.append(
            f"( printf '{esc(b)}\\n'; sleep 5 ) | nc -w 8 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n' > /tmp/rp_p{v}.txt &"
        )
        if v % 4 == 0:
            lines.append("wait")
            lines.append("sleep 1")
    lines.append("wait")
    lines.append("for f in $(ls -v /tmp/rp_p*.txt); do echo \"$f: $(cat $f)\"; done")
    await run(transport, "PAN ver sweep 1-8", "\n".join(lines) + "\ntrue", timeout=90)

    await run(
        transport,
        "SERVER LOG tail",
        'grep -aE "GREETING|MEASUREMENT|version" /tmp/csmsd_run.log | tail -12; true',
        timeout=20,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 27 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
