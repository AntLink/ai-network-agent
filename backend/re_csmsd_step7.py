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

LOG = open("re_csmsd_step7_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 7: LAUNCHER DEBUG + RELAUNCH + EXTENDED POLL")
    out("=" * 70)

    # ---- Phase 1: why did S99csmsd fail? -------------------------------------
    await run(
        transport,
        "DEBUG: start-stop-daemon presence + verbose start attempt",
        """command -v start-stop-daemon || echo "ssd NOT in PATH"
ls -la /sbin/start-stop-daemon 2>/dev/null
rm -f /media/tci/csms/csmsd.pid
/etc/rc5.d/S99csmsd start 2>&1
sleep 3
echo "pidof after ssd: $(pidof csmsd.elf 2>/dev/null || echo none)"
true""",
        timeout=30,
    )

    # ---- Phase 2: try --daemon directly --------------------------------------
    await run(
        transport,
        "TEST: direct --daemon invocation",
        """/media/tci/csms/bin/csmsd.elf --daemon 2>&1 | head -10
echo "rc=$?"
sleep 3
echo "pidof after direct --daemon: $(pidof csmsd.elf 2>/dev/null || echo none)"
true""",
        timeout=40,
    )

    # ---- Phase 3: fallback - proven setsid launch ----------------------------
    await run(
        transport,
        "RELAUNCH: setsid foreground-style (known working)",
        """pidof csmsd.elf >/dev/null 2>&1 || {
  rm -f /tmp/csmsd_run.log
  setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
}
sleep 3
echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
true""",
        timeout=30,
    )

    # ---- Phase 4: extended poll (up to 5 min) ---------------------------------
    await run(
        transport,
        "EXTENDED POLL: listeners every 20s x15",
        """for i in $(seq 1 15); do
  sleep 20
  P=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | tr '\\n' ' ')
  A=$(pidof csmsd.elf 2>/dev/null || echo dead)
  echo "t=$((i*20))s pid=$A listeners: ${P:-none}"
  if [ -n "$P" ]; then echo ">>> PORTS UP at t=$((i*20))s <<<"; break; fi
done
true""",
        timeout=340,
    )

    # ---- Phase 5: SCPI probe ---------------------------------------------------
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

    # ---- Phase 6: log tail ------------------------------------------------------
    await run(
        transport,
        "LOG: csmsd stdout tail",
        "tail -25 /tmp/csmsd_run.log 2>/dev/null; true",
        timeout=25,
    )

    out("\n" + "=" * 70)
    out("  STEP 7 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
