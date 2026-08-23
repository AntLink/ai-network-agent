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
        "ls /bin/ | head -30",
        "ps",
        "df -h 2>/dev/null || df",
        "mount",
        "hostname",
        "uptime",
        "cat /proc/net/dev",
        "cat /proc/net/route",
        "cat /etc/hostname",
        "cat /etc/mtab 2>/dev/null || cat /proc/mounts",
        "ifconfig",
        "netstat -r 2>/dev/null || route",
        "ping -c 1 127.0.0.1",
        "ls /etc/",
        "cat /etc/passwd",
        "date",
        "ls /proc/",
    ]
    
    for cmd in commands:
        try:
            result = await transport.run(cmd)
            print(f"\n=== {cmd} ===")
            print(result[:500])
        except Exception as e:
            print(f"\n=== {cmd} === ERROR: {e}")

asyncio.run(test())
