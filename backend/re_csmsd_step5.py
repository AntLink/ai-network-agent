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

LOG = open("re_csmsd_step5_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 5: OFFICIAL LAUNCHER + PATIENT PORT POLLING")
    out("=" * 70)

    # ---- Phase 1: read the official launcher --------------------------------
    await run(
        transport,
        "LAUNCHER: /etc/rc5.d/S99csmsd content",
        """ls -la /etc/rc5.d/ | grep -i csms
cat /etc/rc5.d/S99csmsd
true""",
        timeout=20,
    )

    # ---- Phase 2: restart via official launcher ------------------------------
    await run(
        transport,
        "RESTART: killall then S99csmsd start",
        """killall csmsd.elf 2>/dev/null; sleep 2
/etc/rc5.d/S99csmsd start
sleep 5
pidof csmsd.elf || true
true""",
        timeout=40,
    )

    # ---- Phase 3: patient port polling ---------------------------------------
    await run(
        transport,
        "POLL: watch for 330x listeners (6 x 10s)",
        """for i in 1 2 3 4 5 6; do
  sleep 10
  P=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | tr '\\n' ' ')
  echo "t=${i}0s listeners: ${P:-none}"
done
true""",
        timeout=90,
    )

    # ---- Phase 4: SCPI probe if ports are up ---------------------------------
    await run(
        transport,
        "SCPI: probe whatever csmsd listens on",
        """PORTS=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | sed 's/.*://' | sort -u)
echo "csmsd ports: ${PORTS:-NONE}"
for p in $PORTS; do
  echo "=== port $p : *IDN? ==="
  printf "*IDN?\\n" | nc -w 4 127.0.0.1 $p 2>/dev/null | head -3
done
true""",
        timeout=60,
    )

    # ---- Phase 5: tail of startup log ----------------------------------------
    await run(
        transport,
        "LOG: last startup lines",
        """tail -40 /media/tci/csms/log/SpectrumMonitor.log 2>/dev/null
echo "--- csmsd stdout ---"
tail -30 /tmp/csmsd_run.log 2>/dev/null
true""",
        timeout=25,
    )

    out("\n" + "=" * 70)
    out("  STEP 5 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
