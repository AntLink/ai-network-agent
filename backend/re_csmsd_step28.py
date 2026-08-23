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

LOG = open("re_csmsd_step28_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=60):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


def hdr(msg_type, subtype=0, ver=0, bodylen=0, marker=0, rver=0):
    return struct.pack("<IIHBBII", marker, 0, msg_type, ver, rver, subtype, bodylen)


def esc(b):
    h = b.hex()
    return "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 28: (cmdVer,respVer) MATRIX FOR GREETING 8565")
    out("=" * 70)

    await run(transport, "SANITY", "pidof csmsd.elf || echo dead", timeout=15)

    matrix = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (2, 2), (3, 3)]
    lines = ["rm -f /tmp/mx_*.txt"]
    i = 0
    for (a, b) in matrix:
        i += 1
        marker = 0xA000 + a * 16 + b
        pkt = hdr(8565, ver=a, bodylen=36, marker=marker, rver=b) + b"\x00" * 36
        lines.append(
            f"( printf '{esc(pkt)}\\n'; sleep 4 ) | nc -w 7 127.0.0.1 3302 2>/dev/null "
            f"| od -A n -t x1 | tr -d ' \\n' > /tmp/mx_{i}_{a}_{b}.txt"
        )
        lines.append("sleep 1")
    lines.append('for f in $(ls -v /tmp/mx_*.txt); do echo "$f => $(cat $f)"; done')
    await run(transport, "MATRIX sweep sequential", "\n".join(lines) + "\ntrue", timeout=120)

    await run(
        transport,
        "SERVER LOG tail",
        'grep -aE "GREETING|MEASUREMENT|bad version|Metrics:" /tmp/csmsd_run.log | tail -14; true',
        timeout=20,
    )

    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 28 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
