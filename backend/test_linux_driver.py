import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from app.repositories.inventory import inventory_repository
from app.drivers.factory import get_driver

device = inventory_repository.get_device("linux-server")
print(f"Device: {device}")

if device:
    driver = get_driver(device)
    print(f"Driver: {driver}")
    
    import asyncio
    async def test():
        try:
            result = await driver.identify()
            print(f"Identify result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(test())
