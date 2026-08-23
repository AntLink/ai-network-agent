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


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    settings.SSH_COMMAND_TIMEOUT = 40

    cmds = {
        "libs of csmsd": "ldd /media/tci/csms/bin/csmsd.elf 2>/dev/null || readelf -d /media/tci/csms/bin/csmsd.elf 2>/dev/null | head -30 || strings /media/tci/csms/bin/csmsd.elf | grep '\\.so' | head -20",
        "lib dirs": "ls -la /media/tci/csms/lib 2>/dev/null; ls /usr/lib/*.so* 2>/dev/null | head -30",
        "other elfs": "find /media /usr/bin /bin /sbin -maxdepth 3 -name '*.elf' -o -maxdepth 3 -name 'ProcessConfig*' 2>/dev/null | head -20",
    }
    for label, cmd in cmds.items():
        print(f"\n===== {label} =====")
        try:
            r = await transport.run(cmd + "; true")
            print(r)
        except Exception as e:
            print(f"ERROR: {e}")


asyncio.run(main())
