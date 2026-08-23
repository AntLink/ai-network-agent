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

LOG = open("re_csmsd_step6_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 6: CLEAN RESTART + LONG POLL FOR LATE PORT BINDING")
    out("=" * 70)

    # ---- Phase 1: current state ---------------------------------------------
    await run(
        transport,
        "STATE: pidof / pidfile / listeners",
        """echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
echo "pidfile: $(cat /media/tci/csms/csmsd.pid 2>/dev/null || echo missing)"
netstat -tlnp 2>/dev/null | grep csmsd || echo "no csmsd listeners"
true""",
        timeout=25,
    )

    # ---- Phase 2: clean stop (wait for full death) ---------------------------
    await run(
        transport,
        "CLEAN STOP: killall + wait until gone + clear stale pidfile",
        """killall csmsd.elf 2>/dev/null
for i in 1 2 3 4 5 6 7 8 9 10; do
  if pidof csmsd.elf >/dev/null 2>&1; then
    echo "still alive (t=${i}s), waiting..."; sleep 1
  else
    echo "csmsd fully dead after ${i}s"; break
  fi
done
pidof csmsd.elf >/dev/null 2>&1 && { echo "forcing SIGKILL"; killall -9 csmsd.elf; sleep 1; }
rm -f /media/tci/csms/csmsd.pid
echo "pidfile cleared"
true""",
        timeout=40,
    )

    # ---- Phase 3: official start (--daemon) ----------------------------------
    await run(
        transport,
        "START: S99csmsd start (official --daemon mode)",
        """/etc/rc5.d/S99csmsd start
sleep 3
echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
echo "pidfile: $(cat /media/tci/csms/csmsd.pid 2>/dev/null || echo missing)"
true""",
        timeout=30,
    )

    # ---- Phase 4: long poll - ports bind late (~60-90s) ----------------------
    await run(
        transport,
        "LONG POLL: watch listeners for up to 3 min",
        """for i in $(seq 1 12); do
  sleep 15
  P=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | tr '\\n' ' ')
  A=$(pidof csmsd.elf 2>/dev/null || echo dead)
  echo "t=$((i*15))s pid=$A listeners: ${P:-none}"
  if [ -n "$P" ]; then echo "PORTS UP at t=$((i*15))s"; break; fi
done
true""",
        timeout=220,
    )

    # ---- Phase 5: SCPI probe on whatever is listening ------------------------
    await run(
        transport,
        "SCPI: *IDN? on live csmsd ports",
        """PORTS=$(netstat -tlnp 2>/dev/null | grep csmsd | awk '{print $4}' | sed 's/.*://' | sort -u)
echo "csmsd ports: ${PORTS:-NONE}"
for p in $PORTS; do
  echo "=== port $p : *IDN? ==="
  printf "*IDN?\\n" | nc -w 5 127.0.0.1 $p 2>/dev/null | head -3
done
true""",
        timeout=90,
    )

    # ---- Phase 6: syslog tail for this boot of csmsd -------------------------
    await run(
        transport,
        "SYSLOG: csmsd messages",
        """grep -i csms /var/volatile/log/messages 2>/dev/null | tail -25
true""",
        timeout=25,
    )

    out("\n" + "=" * 70)
    out("  STEP 6 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
