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
    
    print(f"Connecting to {host} as {username}...")
    transport = SSHTransport(host, username, password)
    
    commands = [
        "uname -a",
        "cat /etc/*release* 2>/dev/null || cat /etc/version 2>/dev/null || echo 'no release file'",
        "hostname",
        "uptime",
        "ip addr show",
    ]
    
    for cmd in commands:
        try:
            result = await transport.run(cmd)
            print(f"\n=== {cmd} ===")
            print(result[:500])
        except Exception as e:
            print(f"\n=== {cmd} === ERROR: {e}")

asyncio.run(test())
