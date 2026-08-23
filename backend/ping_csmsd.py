import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

settings.SSH_COMMAND_TIMEOUT = 15
settings.SSH_CONNECT_TIMEOUT = 15

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    try:
        r = await t.run("pidof csmsd.elf; echo ---; netstat -tlnp 2>/dev/null | grep 330; echo OK")
        print(r)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


asyncio.run(main())
