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

    def _write(self, payload: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def list_devices(self):
        return self._read().get("devices", [])

    def get_device(self, device_id: str):
        return next((d for d in self.list_devices() if d.get("id") == device_id), None)

    def create_device(self, device: dict):
        payload = self._read()
        devices = list(payload.get("devices", []))
        device_id = str(device.get("id", "")).strip()
        if not device_id:
            raise ValueError("Device id is required")
        if self.get_device(device_id):
            raise ValueError(f"Device '{device_id}' already exists")
        devices.append(device)
        payload["devices"] = devices
        self._write(payload)
        return device

    def update_device(self, device_id: str, device: dict):
        payload = self._read()
        devices = list(payload.get("devices", []))
        current_id = str(device_id).strip()
        if not current_id:
            raise ValueError("Device id is required")

        index = next((i for i, item in enumerate(devices) if str(item.get("id", "")).strip() == current_id), None)
        if index is None:
            raise ValueError(f"Device '{current_id}' not found")

        updated_id = str(device.get("id", current_id)).strip() or current_id
        if updated_id != current_id and self.get_device(updated_id):
            raise ValueError(f"Device '{updated_id}' already exists")

        merged = dict(devices[index])
        merged.update(device)
        merged["id"] = updated_id
        devices[index] = merged
        payload["devices"] = devices
        self._write(payload)
        return merged

    def delete_device(self, device_id: str):
        payload = self._read()
        devices = list(payload.get("devices", []))
        current_id = str(device_id).strip()
        if not current_id:
            raise ValueError("Device id is required")

        next_devices = [item for item in devices if str(item.get("id", "")).strip() != current_id]
        if len(next_devices) == len(devices):
            raise ValueError(f"Device '{current_id}' not found")

        payload["devices"] = next_devices
        self._write(payload)
        return {"deleted": current_id}

inventory_repository = InventoryRepository()
