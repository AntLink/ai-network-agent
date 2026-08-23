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

LOG = open("re_csmsd_step10_log.txt", "w", encoding="utf-8", errors="replace")


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
    out("  RE SESSION STEP 10: PORT ROLE MAPPING + CGI COMMS + EXTERNAL ACCESS")
    out("=" * 70)

    # ---- Phase 1: config files with port defs ---------------------------------
    await run(
        transport,
        "CONFIG: XML/conf files mentioning 330x",
        """ls -la /media/tci/csms/etc/
grep -rn "330" /media/tci/csms/etc/ 2>/dev/null | head -30
true""",
        timeout=25,
    )

    # ---- Phase 2: full CSMSConfig.xml ------------------------------------------
    await run(
        transport,
        "CONFIG: CSMSConfig.xml (full)",
        """cat /media/tci/csms/etc/CSMSConfig.xml 2>/dev/null | head -120
true""",
        timeout=25,
    )

    # ---- Phase 3: sqlite db schema/config ---------------------------------------
    await run(
        transport,
        "DB: csmsdb.db tables",
        """which sqlite3 || echo "no sqlite3 cli"
strings /media/tci/csms/data/csmsdb.db 2>/dev/null | grep -iE "port|3302|3303|3307|CREATE TABLE" | head -40
true""",
        timeout=30,
    )

    # ---- Phase 4: how does the web UI talk to csmsd? -----------------------------
    await run(
        transport,
        "CGI: scripts + how they fetch data",
        """ls -la /media/httpd/cgi-bin/ | head -20
for f in /media/httpd/cgi-bin/*; do
  [ -f "$f" ] || continue
  echo "--- $f ---"
  file "$f" | head -1
done
true""",
        timeout=30,
    )

    await run(
        transport,
        "CGI: grep for sockets/ports/shm in cgi-bin",
        """grep -rln "3302\\|3303\\|3307\\|socket\\|ShMem\\|localhost\\|127.0.0.1" /media/httpd/cgi-bin/ 2>/dev/null | head -10
echo "--- shell CGIs ---"
for f in /media/httpd/cgi-bin/*.cgi; do
  [ -f "$f" ] && { echo "### $f"; head -25 "$f"; }
done 2>/dev/null | head -80
true""",
        timeout=35,
    )

    # ---- Phase 5: established connections to csmsd right now ---------------------
    await run(
        transport,
        "NETSTAT: who is connected to 330x?",
        """netstat -tnp 2>/dev/null | grep -E "3302|3303|3307" 
true""",
        timeout=20,
    )

    out("\n" + "=" * 70)
    out("  STEP 10 COMPLETE")
    out("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
