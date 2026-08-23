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

LOG = open("re_csmsd_step20_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  STEP 20: SERVICE RECOVERY AFTER CRASH")
    out("=" * 70)

    # clean any zombies
    await run(
        transport,
        "CLEAN",
        """pkill -f sweep5.sh 2>/dev/null; pkill nc 2>/dev/null
killall -9 csmsd.elf 2>/dev/null; sleep 1
rm -f /media/tci/csms/csmsd.pid
echo cleaned""",
        timeout=25,
    )

    # official start WITH fixed PATH (start-stop-daemon lives in /sbin)
    await run(
        transport,
        "START via S99csmsd with PATH=/sbin",
        """export PATH=/sbin:/usr/sbin:$PATH
/etc/rc5.d/S99csmsd start
sleep 4
echo "pidof: $(pidof csmsd.elf 2>/dev/null || echo none)"
echo "pidfile: $(cat /media/tci/csms/csmsd.pid 2>/dev/null || echo missing)" """.strip(),
        timeout=40,
    )

    # poll for ports (~75s init)
    await run(
        transport,
        "POLL for listeners (up to 2.5 min)",
        """for i in $(seq 1 10); do
  sleep 15
  P=$(netstat -tlnp 2>/dev/null | grep csmsd | wc -l)
  echo "t=$((i*15))s listeners=$P"
  [ "$P" -ge 3 ] && { echo PORTS_UP; break; }
done
true""".strip(),
        timeout=200,
    )

    # verify + also make future restarts easy: create a wrapper script on device
    await run(
        transport,
        "INSTALL restart helper /tmp/csmsd-restart.sh",
        """printf '#!/bin/sh\\nexport PATH=/sbin:/usr/sbin:$PATH\\nkillall csmsd.elf 2>/dev/null\\nsleep 3\\nkillall -9 csmsd.elf 2>/dev/null\\nrm -f /media/tci/csms/csmsd.pid\\n/etc/rc5.d/S99csmsd start\\necho restarted\\n' > /tmp/csmsd-restart.sh
chmod +x /tmp/csmsd-restart.sh
cat /tmp/csmsd-restart.sh""",
        timeout=20,
    )

    r = await run(transport, "FINAL STATE", "pidof csmsd.elf; netstat -tlnp 2>/dev/null | grep csmsd; true", timeout=20)

    out("\n" + "=" * 70)
    out("  STEP 20 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
