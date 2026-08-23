import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
settings.SSH_COMMAND_TIMEOUT = 15

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USERNAME = "root"
PASSWORD = "815m1ll4h"

# Steps are grouped so that "$?" (step 3) is evaluated in the same shell
# as step 2, and each group finishes well within the 15s command timeout.
STEPS = [
    ("STEP 1: Kill any existing csmsd", """\
killall csmsd.elf 2>/dev/null
sleep 1
echo "killall done"
"""),

    ("STEP 2+3: Start csmsd.elf and capture output + exit code", """\
echo "=== Starting csmsd.elf ==="
timeout 10 /media/tci/csms/bin/csmsd.elf 2>&1 | head -50
echo "Exit code: $?"
"""),

    ("STEP 4: Check hostname", """\
echo ""
echo "=== Hostname ==="
hostname
cat /etc/hostname
"""),

    ("STEP 5: License file content", """\
echo ""
echo "=== License File ==="
cat /media/tci/csms/etc/CsmsLicense.lic
"""),

    ("STEP 6: Try changing hostname to match license", """\
echo ""
echo "=== Testing hostname change ==="
hostname CSMS-OM2218076
hostname
"""),

    ("STEP 7: Start csmsd again with new hostname", """\
echo ""
echo "=== Starting csmsd with new hostname ==="
timeout 10 /media/tci/csms/bin/csmsd.elf 2>&1 | head -50
"""),

    ("STEP 8: Check ports after start", """\
echo ""
echo "=== Checking ports ==="
netstat -tlnp 2>/dev/null | grep -E "5025|37000|37001|9999|10001"
"""),

    ("STEP 9: Restore original hostname", """\
echo ""
echo "=== Restoring hostname ==="
hostname CSMS-SINGKAWANG
hostname
"""),
]


LOG = open("csmsd_manual_log.txt", "w", encoding="utf-8", errors="replace")


async def main():
    def out(*args):
        line = " ".join(str(a) for a in args)
        LOG.write(line + "\n")
        LOG.flush()
        print(line, flush=True)

    out("SCRIPT_STARTED")
    transport = SSHTransport(HOST, USERNAME, PASSWORD)

    for label, cmd in STEPS:
        out(f"\n{'#' * 70}")
        out(f"# {label}")
        out(f"{'#' * 70}")
        out(f"$ {cmd.strip()}")
        out("--- OUTPUT " + "-" * 58)
        try:
            result = await transport.run(cmd)
            out(result if result.strip() else "(no stdout)")
        except Exception as e:
            out(f"[ERROR] {type(e).__name__}: {e}")

    out("SCRIPT_FINISHED")


asyncio.run(main())
