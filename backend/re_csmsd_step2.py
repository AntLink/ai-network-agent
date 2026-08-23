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

CSMSD = "/media/tci/csms/bin/csmsd.elf"
LOG = open("re_csmsd_step2_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=20):
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
        out(f"(TIMEOUT after {timeout}s - command still running / channel held open)")
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  RE SESSION STEP 2: DETACHED LAUNCH OF csmsd.elf + PORT/SCPI PROBE")
    out("=" * 70)

    # ---- Phase 1: current state -------------------------------------------
    await run(
        transport,
        "STATE: hostname / csmsd process / listeners",
        """hostname
ps aux | grep -E "csms|spectrum" | grep -v grep || echo "no csms processes"
netstat -tlnp 2>/dev/null || echo "netstat failed\"""",
        timeout=25,
    )

    # ---- Phase 2: clean slate + license-matching hostname ------------------
    await run(
        transport,
        "PREP: kill old csmsd, set license hostname",
        f"""killall csmsd.elf 2>/dev/null; sleep 1
hostname CSMS-OM2218076
echo "hostname now: $(hostname)"
rm -f /tmp/csmsd_run.log""",
        timeout=20,
    )

    # ---- Phase 3: FULLY DETACHED launch ------------------------------------
    # Key fix vs previous session: redirect stdin/stdout/stderr and use setsid,
    # otherwise the SSH exec channel stays open and asyncssh wait_for hangs.
    await run(
        transport,
        "LAUNCH: setsid nohup csmsd.elf (fully detached)",
        f"""setsid sh -c '{CSMSD} >/tmp/csmsd_run.log 2>&1 </dev/null &' 
sleep 2
echo "launched; pidof: $(pidof csmsd.elf)" """.strip(),
        timeout=20,
    )

    # ---- Phase 4: inspect while running ------------------------------------
    await run(
        transport,
        "INSPECT: process / fds / ports / startup log",
        """echo "=== ps ==="
ps aux | grep csmsd | grep -v grep || echo "csmsd NOT running"
echo "=== fds ==="
ls -la /proc/$(pidof csmsd.elf)/fd/ 2>/dev/null | head -25
echo "=== tcp listen ==="
netstat -tlnp 2>/dev/null
echo "=== udp listen ==="
netstat -ulnp 2>/dev/null | head -15
echo "=== startup log (/tmp/csmsd_run.log) ==="
cat /tmp/csmsd_run.log 2>/dev/null | head -60""",
        timeout=30,
    )

    # ---- Phase 5: SCPI probes on candidate ports ---------------------------
    await run(
        transport,
        "SCPI PROBE: *IDN? on candidate ports",
        """for p in 5025 37000 37001 9999 10001; do
  if netstat -tln 2>/dev/null | grep -q ":$p "; then
    echo "--- port $p open, sending *IDN? ---"
    echo "*IDN?" | nc -w 3 127.0.0.1 $p 2>/dev/null | head -5
  else
    echo "--- port $p closed ---"
  fi
done""",
        timeout=40,
    )

    # ---- Phase 6: restore ---------------------------------------------------
    await run(
        transport,
        "RESTORE: hostname back to CSMS-SINGKAWANG",
        'hostname CSMS-SINGKAWANG; echo "restored: $(hostname)"',
        timeout=15,
    )

    out("\n" + "=" * 70)
    out("  STEP 2 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
