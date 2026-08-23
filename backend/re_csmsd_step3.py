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

LOG = open("re_csmsd_step3_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 3: INIT SCRIPT + PROPER RESTART + PORT 330x PROBE")
    out("=" * 70)

    # ---- Phase 1: how does csmsd start at boot? ----------------------------
    await run(
        transport,
        "INIT: find csmsd startup script",
        """grep -rl "csmsd" /etc/init.d/ /etc/rcS.d/ /etc/inittab 2>/dev/null
echo "---"
for f in $(grep -rl "csmsd" /etc/init.d/ /etc/rcS.d/ 2>/dev/null); do
  echo "### $f ###"
  cat "$f"
done""",
        timeout=30,
    )

    # ---- Phase 2: kill my test instance ------------------------------------
    await run(
        transport,
        "CLEANUP: kill test instance",
        """killall csmsd.elf 2>/dev/null; sleep 2
pidof csmsd.elf || echo "no csmsd running\"""",
        timeout=20,
    )

    # ---- Phase 3: restart the boot way --------------------------------------
    # We don't know the init invocation yet; try common patterns and verify.
    await run(
        transport,
        "RESTART: via init script if present",
        """INIT=$(grep -rl "csmsd" /etc/init.d/ 2>/dev/null | head -1)
if [ -n "$INIT" ]; then
  echo "using $INIT"
  "$INIT" stop 2>/dev/null; sleep 1
  "$INIT" start 2>/dev/null || "$INIT" restart 2>/dev/null
else
  echo "no init script found - launching directly"
  setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
fi
sleep 6
echo "=== pidof ==="; pidof csmsd.elf
echo "=== ports ==="; netstat -tlnp 2>/dev/null | grep csmsd""",
        timeout=45,
    )

    # ---- Phase 4: probe 3302/3303/3307 --------------------------------------
    await run(
        transport,
        "PROBE: banner + SCPI on 3302/3303/3307",
        """for p in 3302 3303 3307; do
  echo "=== port $p ==="
  echo "*IDN?" | nc -w 3 127.0.0.1 $p 2>/dev/null | head -5
  echo "(rc=$?)"
done""",
        timeout=40,
    )

    # ---- Phase 5: strings around port numbers -------------------------------
    await run(
        transport,
        "STRINGS: port/protocol hints in binary",
        """strings /media/tci/csms/bin/csmsd.elf | grep -E "\\b330[0-9]\\b" | head -20
echo "---scpi---"
strings /media/tci/csms/bin/csmsd.elf | grep -iE "^\\*(IDN|OPC|RST|CLS)|SCPI|:MEAS|:FREQ|:POW|:INIT|:CONF" | head -40
echo "---listen/bind---"
strings /media/tci/csms/bin/csmsd.elf | grep -iE "listen|bind|socket|port" | head -30""",
        timeout=60,
    )

    out("\n" + "=" * 70)
    out("  STEP 3 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
