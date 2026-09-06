import asyncio
import time as _time

from app.core.audit import log_event
from app.repositories.inventory import inventory_repository
from app.drivers.factory import get_driver

class DeviceService:
    def get_driver(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return get_driver(device)
    async def list_devices(self):
        return inventory_repository.list_devices()

    async def get_device(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return device

    async def identify(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return await get_driver(device).identify()

    async def facts(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return await get_driver(device).get_facts()

    async def interfaces(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return await get_driver(device).get_interfaces()

    async def routes(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return await get_driver(device).get_routes()

    async def config(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return await get_driver(device).get_config()

    async def vlans(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        return await get_driver(device).get_vlans() if hasattr(get_driver(device), 'get_vlans') else {"raw": "not supported"}

    async def services(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        driver = get_driver(device)
        if hasattr(driver, 'get_services'):
            return await driver.get_services()
        return {"raw": "not supported"}

    async def disk(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        driver = get_driver(device)
        if hasattr(driver, 'get_disk'):
            return await driver.get_disk()
        return {"raw": "not supported"}

    async def memory(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        driver = get_driver(device)
        if hasattr(driver, 'get_memory'):
            return await driver.get_memory()
        return {"raw": "not supported"}

    async def ntp(self, device_id: str):
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        driver = get_driver(device)
        if hasattr(driver, 'get_ntp'):
            return await driver.get_ntp()
        return {"raw": "not supported"}

    async def health(self, device_id: str):
        """Reachability + vendor sanity checks (e.g. broken vIOS flash)."""
        import asyncio as _asyncio

        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        driver = get_driver(device)
        if hasattr(driver, "health"):
            return await driver.health()

        # generic TCP reachability probe for drivers without health()
        import socket as _socket
        host = (device.get("management_address") or "").split("/")[0]
        port = int(device.get("management_port") or 22)
        try:
            fut = _asyncio.open_connection(host, port)
            reader, writer = await _asyncio.wait_for(fut, timeout=5.0)
            banner = await _asyncio.wait_for(reader.readline(), timeout=3.0)
            writer.close()
            return {"device_id": device_id, "reachable": True,
                    "ssh_banner": banner.decode(errors="replace").strip()}
        except Exception as e:
            return {"device_id": device_id, "reachable": False, "reason": str(e)}

    async def batch_status(self):
        """Return status, cpu, memory, latency for ALL devices (one call).

        TCP probe → status + latency (fast, ~2-3s total via parallel).
        SSH facts → cpu/memory (only for reachable devices, parallel 10s).
        """
        import asyncio as _asyncio

        devices = inventory_repository.list_devices()
        if not devices:
            return []

        async def _probe(device):
            host = (device.get("management_address") or "").split("/")[0]
            port = int(device.get("management_port") or 22)
            result = {
                "device_id": device["id"],
                "status": "offline",
                "cpu": 0,
                "memory": 0,
                "latency_ms": None,
            }
            try:
                t0 = _time.perf_counter()
                reader, writer = await _asyncio.wait_for(
                    _asyncio.open_connection(host, port), timeout=3.0
                )
                await asyncio.wait_for(reader.readline(), timeout=3.0)
                writer.close()
                latency = int((_time.perf_counter() - t0) * 1000)
                result["status"] = "online"
                result["latency_ms"] = latency
            except Exception:
                result["status"] = "offline"
                return result

            # CPU/Memory — parse from facts output (fast parser, no full SSH session)
            try:
                driver = get_driver(device)
                facts = await driver.get_facts()
                raw = (facts.get("data") or "").lower()
                if "cpu" in raw:
                    import re as _re
                    m = _re.search(r"(\d+(?:\.\d+)?)%", raw)
                    if m:
                        result["cpu"] = int(float(m.group(1)))
                if "memory" in raw:
                    m2 = _re.search(r"(\d+(?:\.\d+)?)%", raw)
                    if m2:
                        result["memory"] = int(float(m2.group(1)))
            except Exception:
                pass
            return result

        results = await _asyncio.gather(*[_probe(d) for d in devices])
        return list(results)

    async def console_exec(self, device_id: str, command: str):
        """Run one command over the telnet console (SSH-broken recovery path)."""
        device = inventory_repository.get_device(device_id)
        if not device:
            raise ValueError("Device not found")
        driver = get_driver(device)
        con_transport = getattr(driver, "_console_transport", None)
        if con_transport is None:
            raise ValueError("Driver does not support console transport")
        con = con_transport()
        if con is None:
            raise ValueError(
                "No console configured for this device "
                "(add console_host/console_port in inventory)"
            )
        out = await con.run(command)
        return {"device_id": device_id, "command": command, "output": out}

device_service = DeviceService()
