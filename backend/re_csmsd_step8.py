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

LOG = open("re_csmsd_step8_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 8: CLEAN DETACHED LAUNCH + POLL PAST 75s INIT")
    out("=" * 70)

    # ---- Phase 1: clean slate -------------------------------------------------
    await run(
        transport,
        "CLEAN: ensure no csmsd running",
        """killall csmsd.elf 2>/dev/null
for i in $(seq 1 10); do
  pidof csmsd.elf >/dev/null 2>&1 || break
  sleep 1
done
pidof csmsd.elf >/dev/null 2>&1 && killall -9 csmsd.elf
sleep 1
echo "pidof now: $(pidof csmsd.elf 2>/dev/null || echo none)"
rm -f /media/tci/csms/csmsd.pid /tmp/csmsd_run.log
true""",
        timeout=35,
    )

    # ---- Phase 2: fully detached launch (no pipes!) ----------------------------
    await run(
        transport,
        "LAUNCH: setsid + full fd redirection",
        """setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
sleep 3
echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
true""",
        timeout=25,
    )

    # ---- Phase 3: poll past the ~75s init window --------------------------------
    await run(
        transport,
        "POLL: every 15s up to 5min",
        """for i in $(seq 1 20); do
  sleep 15
  P=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | tr '\\n' ' ')
  A=$(pidof csmsd.elf 2>/dev/null || echo dead)
  echo "t=$((i*15))s pid=$A listeners: ${P:-none}"
  if [ -n "$P" ]; then echo ">>> PORTS UP at t=$((i*15))s <<<"; break; fi
done
true""",
        timeout=340,
    )

    # ---- Phase 4: SCPI probe -----------------------------------------------------
    await run(
        transport,
        "SCPI: *IDN? on live ports",
        """PORTS=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | sed 's/.*://' | sort -u)
echo "csmsd ports: ${PORTS:-NONE}"
for p in $PORTS; do
  echo "=== port $p ==="
  printf "*IDN?\\n" | nc -w 5 127.0.0.1 $p 2>/dev/null | head -3
done
true""",
        timeout=90,
    )

    # ---- Phase 5: cross-session liveness check (new SSH conn) --------------------
    await run(
        transport,
        "LIVENESS: fresh connection re-check",
        """sleep 5
echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
netstat -tlnp 2>/dev/null | grep csmsd || echo "no listeners"
tail -12 /tmp/csmsd_run.log 2>/dev/null
true""",
        timeout=30,
    )

    out("\n" + "=" * 70)
    out("  STEP 8 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
