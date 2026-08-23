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
    'hostname CSMS-OM2218076 && /media/tci/csms/bin/csmsd.elf & sleep 8; '
    'echo "=== All TCP connections ==="; cat /proc/net/tcp; '
    'echo "=== All TCP6 connections ==="; cat /proc/net/tcp6; '
    'echo "=== csmsd FDs ==="; ls -la /proc/$(pidof csmsd.elf)/fd/ 2>/dev/null; '
    'echo "=== csmsd net ==="; cat /proc/$(pidof csmsd.elf)/net/tcp 2>/dev/null; '
    'echo "=== Try connect to 192.168.162.20:5025 ==="; '
    'echo "*IDN?" | nc -w 3 192.168.162.20 5025 2>/dev/null; '
    'echo "=== Try connect to 192.168.162.20:37000 ==="; '
    'echo "*IDN?" | nc -w 3 192.168.162.20 37000 2>/dev/null; '
    'killall csmsd.elf 2>/dev/null; hostname CSMS-SINGKAWANG; echo done'
)


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  CSMSD BIND CHECK ON 192.168.162.20")
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
