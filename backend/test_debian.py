import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.transports.ssh import SSHTransport

async def test():
    host = "172.23.193.80"
    username = "root"
    password = "815m1ll4h"
    
    print(f"Connecting to {host} as {username}...")
    transport = SSHTransport(host, username, password)
    
    commands = [
        "cat /etc/os-release",
        "uname -a",
        "hostname",
        "uptime",
        "ip addr show",
        "ip route show",
        "cat /etc/network/interfaces",
        "systemctl list-units --type=service --state=running 2>/dev/null | head -20",
        "df -h",
        "free -m",
    ]
    
    for cmd in commands:
        try:
            result = await transport.run(cmd)
            print(f"\n=== {cmd} ===")
            print(result[:800])
        except Exception as e:
            print(f"\n=== {cmd} === ERROR: {e}")

asyncio.run(test())
