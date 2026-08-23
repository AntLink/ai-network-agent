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

LOG = open("re_csmsd_step12_log.txt", "w", encoding="utf-8", errors="replace")


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


def hdr_hex(msg_type, status=0, bodylen=0, f0=0, f4=0, va=0, vb=0):
    return struct.pack("<IIHBBII", f0, f4, msg_type, va, vb, status, bodylen).hex()


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 12: MSGTYPE SWEEP ON 3302/3303/3307")
    out("=" * 70)

    def send_probe(port, hx):
        esc = "\\x" + "\\x".join(hx[i:i + 2] for i in range(0, len(hx), 2))
        return (
            f"printf '{esc}\\n' | timeout 2 nc 127.0.0.1 {port} 2>/dev/null "
            f"| od -A x -t x1 | head -6; echo ---"
        )

    # ---- sweep msgTypes 0..31 on 3302 ---------------------------------------
    for start in range(0, 32, 8):
        cmds = []
        for t in range(start, start + 8):
            hx = hdr_hex(t)
            esc = "\\x" + "\\x".join(hx[i:i + 2] for i in range(0, len(hx), 2))
            cmds.append(
                f'echo "type={t}:"; '
                f"printf '{esc}\\n' | timeout 2 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1 | head -4"
            )
        await run(transport, f"SWEEP 3302 types {start}-{start+7}", "\n".join(cmds) + "\ntrue", timeout=60)

    # ---- a few interesting types with body (e.g., version handshake?) --------
    # try flag bytes = common versions 1..4 on type 1..3
    cmds = []
    for t in (1, 2, 3):
        for v in (1, 2):
            hx = hdr_hex(t, va=v)
            esc = "\\x" + "\\x".join(hx[i:i + 2] for i in range(0, len(hx), 2))
            cmds.append(
                f'echo "type={t} ver={v}:"; '
                f"printf '{esc}\\n' | timeout 2 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1 | head -6"
            )
    await run(transport, "VERSION FLAGS on types 1-3", "\n".join(cmds) + "\ntrue", timeout=90)

    # ---- probe ports 3303 (VCP) and 3307 --------------------------------------
    for port in (3303, 3307):
        cmds = []
        for t in (0, 1, 2, 3):
            hx = hdr_hex(t)
            esc = "\\x" + "\\x".join(hx[i:i + 2] for i in range(0, len(hx), 2))
            cmds.append(
                f'echo "type={t}:"; '
                f"printf '{esc}\\n' | timeout 2 nc 127.0.0.1 {port} 2>/dev/null | od -A x -t x1 | head -4"
            )
        await run(transport, f"PROBE port {port}", "\n".join(cmds) + "\ntrue", timeout=60)

    # ---- health -----------------------------------------------------------------
    await run(transport, "HEALTH", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 12 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    import struct
    asyncio.run(main())
