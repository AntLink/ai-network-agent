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

LOG = open("re_csmsd_step9_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=25):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n{'=' * 70}")
    out(f"[{label}]  (timeout={timeout}s)")
    out(f"$ {cmd.strip()}")
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


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  RE SESSION STEP 9: PER-PORT PROTOCOL PROBES (3302 / 3303 / 3307)")
    out("=" * 70)

    # Quick sanity: service still up?
    await run(
        transport,
        "SANITY: csmsd alive + ports",
        """pidof csmsd.elf || echo dead
netstat -tlnp 2>/dev/null | grep csmsd || true""",
        timeout=20,
    )

    # ---- Port 3302 ----------------------------------------------------------
    await run(
        transport,
        "PORT 3302: SCPI *IDN? test",
        """printf "*IDN?\\n" | timeout 6 nc 127.0.0.1 3302 2>/dev/null | head -c 300 | od -c | head -10
true""",
        timeout=20,
    )
    await run(
        transport,
        "PORT 3302: banner grab (connect only)",
        """timeout 4 nc 127.0.0.1 3302 </dev/null 2>/dev/null | head -c 200 | od -c | head -8
true""",
        timeout=18,
    )

    # ---- Port 3303 ----------------------------------------------------------
    await run(
        transport,
        "PORT 3303: SCPI *IDN? test",
        """printf "*IDN?\\n" | timeout 6 nc 127.0.0.1 3303 2>/dev/null | head -c 300 | od -c | head -10
true""",
        timeout=20,
    )
    await run(
        transport,
        "PORT 3303: banner grab (connect only)",
        """timeout 4 nc 127.0.0.1 3303 </dev/null 2>/dev/null | head -c 200 | od -c | head -8
true""",
        timeout=18,
    )

    # ---- Port 3307 ----------------------------------------------------------
    await run(
        transport,
        "PORT 3307: SCPI *IDN? test",
        """printf "*IDN?\\n" | timeout 6 nc 127.0.0.1 3307 2>/dev/null | head -c 300 | od -c | head -10
true""",
        timeout=20,
    )
    await run(
        transport,
        "PORT 3307: banner grab (connect only)",
        """timeout 4 nc 127.0.0.1 3307 </dev/null 2>/dev/null | head -c 200 | od -c | head -8
true""",
        timeout=18,
    )

    # ---- Protocol hints from binary for these ports ---------------------------
    await run(
        transport,
        "STRINGS: context around ports 330x + protocol names",
        """strings /media/tci/csms/bin/csmsd.elf | grep -iE "3302|3303|3307|CommandNet|CtrlNet|DataNet|RdsNet|AudioNet|SpectrumNet|ClientPort|ServerPort" | head -30
true""",
        timeout=40,
    )

    # ---- Final state check -----------------------------------------------------
    await run(
        transport,
        "FINAL: csmsd still healthy",
        """pidof csmsd.elf || echo dead
netstat -tlnp 2>/dev/null | grep csmsd || true
true""",
        timeout=20,
    )

    out("\n" + "=" * 70)
    out("  STEP 9 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
