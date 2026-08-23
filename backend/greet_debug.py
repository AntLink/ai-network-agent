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

    # greet with body, then dump ALL related log lines
    pkt = struct.pack("<IIHBBII", 0xC002, 0, 8565, 0, 0, 0, 36) + b"\x00" * 36
    h = pkt.hex()
    esc = "\\x" + "\\x".join(h[i:i + 2] for i in range(0, len(h), 2))
    cmd = f"""( printf '{esc}\\n'; sleep 5 ) | nc -w 10 127.0.0.1 3302 2>/dev/null | od -A x -t x1z | head -12
echo '--- log tail ---'
tail -25 /tmp/csmsd_run.log
true"""
    r = await t.run(cmd)
    print(r)


asyncio.run(main())
