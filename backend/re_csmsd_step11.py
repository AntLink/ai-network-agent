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

LOG = open("re_csmsd_step11_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=25):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n{'=' * 70}")
    out(f"[{label}]")
    out("-" * 70)
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except asyncio.TimeoutError:
        out(f"(TIMEOUT after {timeout}s)")
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


def mkhdr(f0=0, f4=0, msg_type=0, flag_a=0, flag_b=0, status=0, bodylen=0):
    return struct.pack("<IIBBHI I".replace(" ", ""), f0, f4, msg_type, flag_a, flag_b, status, bodylen)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 11: LIVE BINARY PROBES AGAINST PORT 3302 (EquipCtrl)")
    out("=" * 70)

    # sanity
    await run(
        transport,
        "SANITY",
        "pidof csmsd.elf && netstat -tlnp 2>/dev/null | grep csmsd; true",
        timeout=15,
    )

    # Probe A: all-zero 20-byte header + \n
    hdr = mkhdr()
    hx = hdr.hex()
    await run(
        transport,
        f"PROBE A: zero-header (msgType=0) -> {hx}",
        f"""printf '{ "\\x" + "\\x".join(hx[i:i+2] for i in range(0, len(hx), 2)) }\\n' | timeout 5 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1z | head -12
true""",
        timeout=20,
    )

    # Probe B: unknown msgType=0xFFFF
    hdr = mkhdr(msg_type=0xFFFF)
    hx = hdr.hex()
    await run(
        transport,
        f"PROBE B: msgType=0xFFFF -> {hx}",
        f"""printf '{ "\\x" + "\\x".join(hx[i:i+2] for i in range(0, len(hx), 2)) }\\n' | timeout 5 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1z | head -12
true""",
        timeout=20,
    )

    # Probe C: msgType=1
    hdr = mkhdr(msg_type=1)
    hx = hdr.hex()
    await run(
        transport,
        f"PROBE C: msgType=1 -> {hx}",
        f"""printf '{ "\\x" + "\\x".join(hx[i:i+2] for i in range(0, len(hx), 2)) }\\n' | timeout 5 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1z | head -12
true""",
        timeout=20,
    )

    # Probe D: pure garbage 21 bytes
    await run(
        transport,
        "PROBE D: 21 garbage bytes",
        """printf 'AAAAAAAAAAAAAAAAAAAAA\\n' | timeout 5 nc 127.0.0.1 3302 2>/dev/null | od -A x -t x1z | head -12
true""",
        timeout=20,
    )

    # Check csmsd log reactions
    await run(
        transport,
        "LOG: csmsd reaction to probes",
        """tail -30 /tmp/csmsd_run.log 2>/dev/null
grep -iE "equip|invalid|error|client" /tmp/csmsd_run.log 2>/dev/null | tail -15
true""",
        timeout=20,
    )

    # service health after probes
    await run(
        transport,
        "HEALTH: csmsd still alive?",
        "pidof csmsd.elf || echo dead; netstat -tln 2>/dev/null | grep 330 || true",
        timeout=15,
    )

    out("\n" + "=" * 70)
    out("  STEP 11 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
