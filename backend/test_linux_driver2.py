import os
import sys
sys.path.insert(0, ".")
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

print(f"LINUX_SERVER_USERNAME: {os.getenv('LINUX_SERVER_USERNAME')}")
print(f"LINUX_SERVER_PASSWORD: {os.getenv('LINUX_SERVER_PASSWORD')}")

from app.repositories.inventory import inventory_repository
from app.drivers.factory import get_driver

device = inventory_repository.get_device("linux-server")
print(f"Device: {device}")

if device:
    driver = get_driver(device)
    print(f"Driver type: {type(driver)}")
    
    # Check what credentials the driver will use
    prefix = device["id"].upper().replace("-", "_")
    username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "root"))
    password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD"))
    print(f"Will use: {username} / {password}")
    
    import asyncio
    async def test():
        try:
            result = await driver.identify()
            print(f"Identify result: {result}")
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(test())
