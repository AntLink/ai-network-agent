import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 30
settings.SSH_CONNECT_TIMEOUT = 30

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMANDS = {
    "Command 1: Current csmsd status": """ps aux | grep csms
ls -la /media/tci/csms/bin/csmsd.elf
file /media/tci/csms/bin/csmsd.elf
true""",

    "Command 2: Why csmsd is not running": """cat /var/volatile/log/messages | grep -i csms | tail -20
cat /media/tci/csms/logs/*.log 2>/dev/null | tail -20
ls -la /media/tci/csms/logs/ 2>/dev/null
true""",

    "Command 3: Dependencies": """ldd /media/tci/csms/bin/csmsd.elf 2>/dev/null || echo "ldd not available"
strings /media/tci/csms/bin/csmsd.elf | grep -iE "config|xml|license" | head -20
true""",

    "Command 4: License file": """ls -la /media/tci/csms/etc/CsmsLicense.lic 2>/dev/null
cat /media/tci/csms/etc/CsmsLicense.lic 2>/dev/null | head -20
true""",

    "Command 5: csmsd config": """cat /media/tci/csms/etc/CSMSConfig.xml 2>/dev/null | head -50
true""",

    "Command 6: Try to start csmsd (dry run / test)": """command -v timeout || echo "NO_TIMEOUT_BINARY"
timeout -s KILL 8 /media/tci/csms/bin/csmsd.elf --help > /tmp/csmsd_help.out 2>&1; echo "help_exit_code=$?"
head -20 /tmp/csmsd_help.out
timeout -s KILL 5 /media/tci/csms/bin/csmsd.elf --version > /tmp/csmsd_ver.out 2>&1; echo "version_exit_code=$?"
head -10 /tmp/csmsd_ver.out
rm -f /tmp/csmsd_help.out /tmp/csmsd_ver.out
true""",

    "Command 7: Ports csmsd would use": """strings /media/tci/csms/bin/csmsd.elf | grep -E "^[0-9]{4,5}$" | head -20
strings /media/tci/csms/bin/csmsd.elf | grep -iE "port|listen|bind" | head -20
true""",

    "Command 8: SCPI strings": """strings /media/tci/csms/bin/csmsd.elf | grep -iE "SCPI|MEAS|FREQ|POW|SWEEP|INIT|CONF" | head -30
true""",
}


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  CSMSD STARTABILITY CHECK ON 192.168.162.20")
    print("=" * 70)

    for label, cmd in COMMANDS.items():
        print(f"\n{'=' * 70}")
        print(f"  {label}")
        print(f"{'=' * 70}")
        try:
            result = await transport.run(cmd)
            print(result if result.strip() else "  (no output)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'=' * 70}")
    print("  CHECK COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
