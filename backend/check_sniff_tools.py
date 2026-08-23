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

    cmd = """echo "=== sniff tools ==="
for b in tcpdump tcpflow tshark dumpcap ngrep socat strace ltrace gdb; do
  command -v $b >/dev/null 2>&1 && echo "$b: YES $(command -v $b)" || echo "$b: no"
done
echo "=== busybox apps ==="
busybox 2>/dev/null | head -3
echo "=== internet check ==="
timeout 5 wget -q -O /dev/null http://google.com && echo NET_OK || echo NET_FAIL
echo "=== arch ==="
uname -m"""
    r = await t.run(cmd + "; true")
    print(r)


asyncio.run(main())
