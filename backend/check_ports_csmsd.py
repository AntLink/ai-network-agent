import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 25
settings.SSH_CONNECT_TIMEOUT = 25

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMAND = (
    'hostname CSMS-OM2218076 && /media/tci/csms/bin/csmsd.elf & CPID=$!; sleep 8; '
    'echo "=== csmsd PID ==="; ps aux | grep csmsd | grep -v grep; '
    'echo "=== TCP ports ==="; netstat -tlnp 2>/dev/null; '
    'echo "=== UDP ports ==="; netstat -ulnp 2>/dev/null; '
    'echo "=== Try SCPI ==="; echo "*IDN?" | nc -w 3 localhost 5025 2>/dev/null; '
    'echo "=== Kill ==="; kill $CPID 2>/dev/null; hostname CSMS-SINGKAWANG; echo done'
)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  CSMSD PORT CHECK ON 192.168.162.20")
    print("=" * 70)

    try:
        result = await transport.run(COMMAND)
        print(result if result.strip() else "(no output)")
    except Exception as e:
        print(f"ERROR: {e}")

    print("=" * 70)
    print("  CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
