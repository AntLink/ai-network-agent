import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.transports.ssh import SSHTransport

async def test():
    host = "192.168.162.20"
    username = "root"
    password = "815m1ll4h"
    
    transport = SSHTransport(host, username, password)
    
    commands = [
        "ifconfig 2>/dev/null || cat /proc/net/dev",
        "route -n 2>/dev/null || cat /proc/net/route",
        "cat /etc/network/interfaces 2>/dev/null || echo 'no interfaces file'",
    ]
    
    for cmd in commands:
        try:
            result = await transport.run(cmd)
            print(f"\n=== {cmd} ===")
            print(result[:1000])
        except Exception as e:
            print(f"\n=== {cmd} === ERROR: {e}")

asyncio.run(test())
