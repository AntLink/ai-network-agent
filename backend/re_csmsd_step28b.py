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

LOG = open("re_csmsd_step28b_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def probe(transport, tag, msg_type, ver, rver):
    marker = 0xA000 + ver * 16 + rver
    pkt = struct.pack("<IIHBBII", marker, 0, msg_type, ver, rver, 0, 36) + b"\x00" * 36
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    cmd = (
        f"printf '{esc}\\n' | nc -w 6 127.0.0.1 3302 2>/dev/null "
        f"| od -A n -t x1 | tr -d ' \\n'"
    )
    settings.SSH_COMMAND_TIMEOUT = 20
    try:
        r = await transport.run(cmd)
        resp = (r or "").strip()
        if len(resp) >= 40:
            errh = resp[24:32]
            err = int(errh[6:] + errh[4:6], 16) if len(errh) == 8 else -1
            echo = int(resp[0:8], 16)
            out(f"  {tag}: reply {len(resp)//2}B echo=0x{echo:x} err={err}")
        else:
            out(f"  {tag}: SILENT ({len(resp)//2}B)")
    except Exception as e:
        out(f"  {tag}: ERROR {type(e).__name__}")


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    out("=" * 70)
    out("  STEP 28b: GREETING VERSION MATRIX")
    out("=" * 70)

    for (a, b) in [(0, 1), (0, 2), (0, 3), (1, 1), (2, 2), (3, 3)]:
        await probe(transport, f"greet cmdVer={a} respVer={b}", 8565, a, b)

    out("-" * 50)
    for (a, b) in [(0, 0), (0, 1), (1, 1), (2, 2)]:
        await probe(transport, f"pan cmdVer={a} respVer={b}", 8563, a, b)

    out("\ndone")


if __name__ == "__main__":
    asyncio.run(main())
