import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 25
    cmd = """echo "=== conn state counts ==="
netstat -tn 2>/dev/null | grep 3302 | awk '{print $6}' | sort | uniq -c
echo "=== all 3302 conns ==="
netstat -tnp 2>/dev/null | grep 3302 | head -25
echo "=== local connect test ==="
timeout 3 nc -z 127.0.0.1 3302 && echo CONNECT_OK || echo CONNECT_FAIL
echo "=== health ==="
pidof csmsd.elf || echo dead
"""
    try:
        r = await t.run(cmd + "true")
        print(r)
    except Exception as e:
        print(f"ERROR: {e}")


asyncio.run(main())
