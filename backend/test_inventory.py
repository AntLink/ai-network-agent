import sys
sys.path.insert(0, ".")
from app.core.config import settings
from app.repositories.inventory import inventory_repository
from app.drivers.factory import get_driver

print(f"Inventory file: {settings.INVENTORY_FILE}")
print(f"Devices: {inventory_repository.list_devices()}")

device = inventory_repository.get_device("mikrotik-rb4011")
print(f"Device: {device}")

if device:
    driver = get_driver(device)
    print(f"Driver: {driver}")
    print(f"Driver vendor: {driver.device.get('vendor')}")
