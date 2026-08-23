import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 10
settings.SSH_CONNECT_TIMEOUT = 10

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMANDS = {
    "a) Kill any running csmsd": "killall csmsd.elf 2>/dev/null; echo killed",
    "b) License file (first 3 lines)": "cat /media/tci/csms/etc/CsmsLicense.lic | head -3",
    "c) Set hostname to CSMS-OM2218076": "hostname CSMS-OM2218076; hostname",
    "d) Start csmsd, verify process/ports, restore hostname":
        "/media/tci/csms/bin/csmsd.elf & sleep 5; ps aux | grep csmsd | grep -v grep; netstat -tlnp 2>/dev/null; hostname CSMS-SINGKAWANG",
}


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print("  CSMSD START ON 192.168.162.20")
    print("=" * 70)

    for label, cmd in COMMANDS.items():
        print(f"\n{'=' * 70}")
        print(f"  {label}")
        print(f"  CMD: {cmd}")
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
