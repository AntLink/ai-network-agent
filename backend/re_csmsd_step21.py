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

LOG = open("re_csmsd_step21_log.txt", "w", encoding="utf-8", errors="replace")


def out(*args):
    line = " ".join(str(a) for a in args)
    LOG.write(line + "\n")
    LOG.flush()
    print(line, flush=True)


async def run(transport, label, cmd, timeout=30):
    settings.SSH_COMMAND_TIMEOUT = timeout
    out(f"\n[{label}]")
    try:
        result = await transport.run(cmd)
        out(result if result.strip() else "(no output)")
        return result
    except Exception as e:
        out(f"[ERROR] {type(e).__name__}: {e}")
    return None


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    out("=" * 70)
    out("  STEP 21: DIAGNOSE + RELAUNCH FOREGROUND")
    out("=" * 70)

    await run(
        transport,
        "STATE + SYSLOG tail",
        """echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
grep -iE "csmsd|segfault|panic" /var/volatile/log/messages 2>/dev/null | tail -12
tail -20 /media/tci/csms/log/SpectrumMonitor.log 2>/dev/null
true""",
        timeout=30,
    )

    # clean then launch foreground-style (proven)
    await run(
        transport,
        "CLEAN",
        """killall -9 csmsd.elf 2>/dev/null; sleep 1
rm -f /media/tci/csms/csmsd.pid /tmp/csmsd_run.log
echo cleaned""",
        timeout=20,
    )

    await run(
        transport,
        "LAUNCH foreground detached",
        """setsid sh -c '/media/tci/csms/bin/csmsd.elf >/tmp/csmsd_run.log 2>&1 </dev/null &'
sleep 3
echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)" """.strip(),
        timeout=25,
    )

    await run(
        transport,
        "POLL ports",
        """for i in $(seq 1 8); do
  sleep 15
  P=$(netstat -tlnp 2>/dev/null | grep csmsd | wc -l)
  A=$(pidof csmsd.elf 2>/dev/null || echo dead)
  echo "t=$((i*15))s pid=$A listeners=$P"
  [ "$P" -ge 3 ] && { echo PORTS_UP; break; }
done
true""".strip(),
        timeout=160,
    )

    await run(
        transport,
        "LOG tail",
        "tail -15 /tmp/csmsd_run.log; true",
        timeout=20,
    )

    r = await run(transport, "FINAL", "pidof csmsd.elf || echo dead", timeout=15)

    out("\n" + "=" * 70)
    out("  STEP 21 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
