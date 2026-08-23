import json
from pathlib import Path
from app.core.config import settings

class InventoryRepository:
    def __init__(self):
        self.path = Path(settings.INVENTORY_FILE)

    def _read(self):
        if not self.path.exists():
            return {"devices": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def list_devices(self):
        return self._read().get("devices", [])

    def get_device(self, device_id: str):
        return next((d for d in self.list_devices() if d.get("id") == device_id), None)

inventory_repository = InventoryRepository()
