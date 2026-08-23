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

LOG = open("re_csmsd_step4_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 4: RESTORE SERVICE + LIVE PROBE PORTS 3302/3303/3307")
    out("=" * 70)

    # ---- Phase 1: restart csmsd (service restore) ---------------------------
    await run(
        transport,
        "RESTART: launch csmsd detached (as before)",
        """killall csmsd.elf 2>/dev/null; sleep 1
rm -f /tmp/csmsd_run.log
setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
sleep 8
echo "=== pidof ==="; pidof csmsd.elf || true
echo "=== ports ==="; netstat -tlnp 2>/dev/null | grep -E "csmsd|330" || echo "no 330x listeners"
true""",
        timeout=40,
    )

    # ---- Phase 2: SCPI probe on live ports ----------------------------------
    await run(
        transport,
        "SCPI: *IDN? on each live port",
        """for p in 3302 3303 3304 3305 3307; do
  if netstat -tln 2>/dev/null | grep -q ":$p "; then
    echo "=== port $p : *IDN? ==="
    printf "*IDN?\\n" | nc -w 4 127.0.0.1 $p 2>/dev/null | head -3
  else
    echo "=== port $p closed ==="
  fi
done
true""",
        timeout=60,
    )

    # ---- Phase 3: banner grab without sending anything -----------------------
    await run(
        transport,
        "BANNER: connect-only grab",
        """for p in 3302 3303 3307; do
  echo "=== port $p banner ==="
  timeout 3 nc 127.0.0.1 $p </dev/null 2>/dev/null | head -c 200 | od -c | head -6
done
true""",
        timeout=45,
    )

    # ---- Phase 4: boot mechanism hunt ----------------------------------------
    await run(
        transport,
        "BOOT: where does csmsd start from?",
        """grep -r "csms" /etc/inittab /etc/init.d/rcS /etc/profile /etc/rcS.d/* 2>/dev/null | head -10
echo "--- SpectrumMonitor script ---"
ls -la /media/tci/SpectrumMonitor 2>/dev/null
head -40 /media/tci/SpectrumMonitor 2>/dev/null
echo "--- crontab ---"
crontab -l 2>/dev/null | head -10
true""",
        timeout=30,
    )

    # ---- Phase 5: final state -------------------------------------------------
    await run(
        transport,
        "FINAL: service state + startup log",
        """ps aux | grep -E "csmsd|csmsAudio" | grep -v grep || true
netstat -tlnp 2>/dev/null | grep csmsd || true
echo "--- log ---"
cat /tmp/csmsd_run.log 2>/dev/null | head -30
true""",
        timeout=25,
    )

    out("\n" + "=" * 70)
    out("  STEP 4 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
