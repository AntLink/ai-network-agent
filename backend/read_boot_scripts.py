import asyncio
import sys

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv("C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\backend\\.env")

from app.core.config import settings

from app.transports.ssh import SSHTransport


async def main():
    t = SSHTransport("192.168.162.20", "root", "815m1ll4h")
    settings.SSH_COMMAND_TIMEOUT = 30

    cmd = r"""echo "=== ifplugdnet.sh ==="
cat /media/httpd/cgi-bin/ifplugdnet.sh
echo ""
echo "=== S18tcinet ==="
cat /etc/rc5.d/S18tcinet
echo ""
echo "=== S25tcistartup ==="
cat /etc/rc5.d/S25tcistartup
true"""
    out = open("boot_scripts_out.txt", "w", encoding="utf-8", errors="replace")
    async with asyncio.timeout(60):
        r = await t.run(cmd)
    out.write(r or "")
    out.close()
    print("written", len(r or ""))


asyncio.run(main())
