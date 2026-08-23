import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 20
settings.SSH_CONNECT_TIMEOUT = 20

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

CSMSD_BIN = "/media/tci/csms/bin/csmsd.elf"
CSMSD_TIMEOUT = 15


async def run_labeled(transport: SSHTransport, label: str, command: str):
    print()
    print("-" * 70)
    print(f"[{label}]")
    print(f"$ {command}")
    print("-" * 70)
    try:
        result = await transport.run(command)
        print(result if result.strip() else "(no output)")
    except asyncio.TimeoutError:
        print(
            f"(no exit within {settings.SSH_COMMAND_TIMEOUT}s -> killed "
            f"by timeout; startup messages above are all we got)"
        )
    except Exception as e:
        print(f"ERROR: {e}")


async def main():
    transport = SSHTransport(HOST, USER, PASS)

    print("=" * 70)
    print(f"  DEBUG csmsd.elf ON {HOST} (user: {USER})")
    print("=" * 70)

    # Step A: temporarily rename host to CSMS-OM2218076
    await run_labeled(
        transport,
        "STEP A: set hostname to CSMS-OM2218076",
        'hostname CSMS-OM2218076; echo "Hostname: $(hostname)"',
    )

    # Step B: launch csmsd.elf in foreground; kill it via timeout
    settings.SSH_COMMAND_TIMEOUT = CSMSD_TIMEOUT
    await run_labeled(
        transport,
        f"STEP B: run {CSMSD_BIN} (timeout {CSMSD_TIMEOUT}s)",
        f"{CSMSD_BIN} 2>&1",
    )
    settings.SSH_COMMAND_TIMEOUT = 20

    # Step C: restore original hostname
    await run_labeled(
        transport,
        "STEP C: restore hostname to CSMS-SINGKAWANG",
        'hostname CSMS-SINGKAWANG; echo "Restored: $(hostname)"',
    )

    print()
    print("=" * 70)
    print("  DEBUG COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
