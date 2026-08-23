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

STEPS = [
    ("Step 1: Start csmsd.elf in background", """\
/media/tci/csms/bin/csmsd.elf &
sleep 5
true"""),

    ("Step 2: Check if running", """\
ps aux | grep csmsd.elf | grep -v grep
true"""),

    ("Step 3: Check ports", """\
netstat -tlnp 2>/dev/null | grep -E "5025|37000|37001"
true"""),

    ("Step 4: Test SCPI connection (*IDN?)", """\
echo "*IDN?" | nc -w 2 localhost 5025
true"""),

    ("Step 5: Test frequency measurement", """\
echo "MEAS:FREQ?" | nc -w 2 localhost 5025
true"""),

    ("Step 6: Test power measurement", """\
echo "MEAS:POW?" | nc -w 2 localhost 5025
true"""),

    ("Step 7: Test sweep", """\
echo "SWEEP:DATA?" | nc -w 2 localhost 5025 | head -c 200
true"""),
]


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  SCPI TEST ON 192.168.162.20 (csmsd.elf)")
    print("=" * 70)

    for label, cmd in STEPS:
        print(f"\n{'-' * 70}")
        print(f"  {label}")
        print(f"  CMD: {cmd.splitlines()[0]}")
        print(f"{'-' * 70}")
        try:
            result = await transport.run(cmd)
            print(result if result.strip() else "  (no output)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'=' * 70}")
    print("  SCPI TEST COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
