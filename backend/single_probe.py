import asyncio
import sys
import struct

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 60

    pkt = struct.pack("<IIHBBII", 0xA001, 0, 8565, 0, 1, 0, 36) + b"\x00" * 36
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    cmd = (
        f"date; ( printf '{esc}\\n'; sleep 4 ) | nc -w 10 127.0.0.1 3302 2>/dev/null "
        f"| od -A x -t x1z | head -20; date; true"
    )
    try:
        r = await t.run(cmd)
        print(r)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")


asyncio.run(main())
