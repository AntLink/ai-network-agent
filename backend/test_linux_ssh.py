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
    
    try:
        result = await transport.run("cat /etc/os-release")
        print(f"OK: {result[:500]}")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
