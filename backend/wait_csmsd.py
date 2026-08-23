import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 15
settings.SSH_CONNECT_TIMEOUT = 15

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMANDS = {
    "a) csmsd process check (after 10s wait)": "sleep 10; ps aux | grep csmsd | grep -v grep",
    "b) TCP listeners": "netstat -tlnp 2>/dev/null",
    "c) UDP listeners": "netstat -ulnp 2>/dev/null",
    "d) csmsd.elf file descriptors": "ls -la /proc/$(pidof csmsd.elf)/fd/ 2>/dev/null | head -20",
    "e) csmsd.elf /proc/net/tcp": "cat /proc/$(pidof csmsd.elf)/net/tcp 2>/dev/null | head -10",
    "f) recent syslog messages": "tail -30 /var/volatile/log/messages 2>/dev/null",
}


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  WAIT + INSPECT CSMSD ON 192.168.162.20")
    print("=" * 70)

    for label, cmd in COMMANDS.items():
        print(f"\n{'=' * 70}")
        print(f"  {label}")
        print(f"  $ {cmd}")
        print(f"{'=' * 70}")
        try:
            result = await transport.run(cmd)
            print(result if result.strip() else "  (no output)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\n{'=' * 70}")
    print("  DONE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
