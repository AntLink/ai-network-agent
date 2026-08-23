import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv(r"C:\Users\mohfa\PycharmProjects\ai-network-agent\backend\.env")

from app.transports.ssh import SSHTransport

HOST = "192.168.162.20"
USER = "root"
PASS = "815m1ll4h"

COMMANDS = [
    "cat /etc/inittab",
    "ls /etc/init.d/",
    "cat /etc/init.d/rcS",
    "cat /etc/init.d/rc",
    "ls -la /media/httpd/cgi-bin/cloudflared",
    "cat /etc/fstab",
    "mount | grep media",
    "ls /etc/rcS.d/ 2>/dev/null || ls /etc/rc.d/ 2>/dev/null || echo 'no rc dirs found'",
    "cat /etc/rc5.d/S* 2>/dev/null | head -50 || echo 'no rc5.d'",
]


async def main():
    transport = SSHTransport(HOST, USER, PASS)
    for cmd in COMMANDS:
        print(f"\n{'='*60}")
        print(f"CMD: {cmd}")
        print(f"{'='*60}")
        try:
            output = await transport.run(cmd)
            print(output)
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
