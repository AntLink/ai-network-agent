import asyncio
import os
import sys
sys.path.insert(0, ".")
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

from app.transports.ssh import SSHTransport

async def test():
    host = "192.168.162.20"
    username = os.getenv("LINUX_SERVER_USERNAME", "root")
    password = os.getenv("LINUX_SERVER_PASSWORD")
    
    print(f"Connecting to {host} as {username}...")
    transport = SSHTransport(host, username, password)
    
    try:
        result = await transport.run("uname -a")
        print(f"OK: {result}")
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
