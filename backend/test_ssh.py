import asyncio
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.transports.ssh import SSHTransport

async def test():
    host = "36.88.39.234"
    username = "ozan"
    password = "815m1ll4h"
    
    print(f"Connecting to {host} as {username}...")
    transport = SSHTransport(host, username, password)
    
    try:
        result = await transport.run("/system identity print")
        print(f"OK: {result}")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
