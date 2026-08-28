import os
from app.drivers.base import BaseDriver
from app.transports.ssh import SSHTransport

class GenericSSHDriver(BaseDriver):
    def _transport(self):
        port = int(self.device.get("management_port") or 22)
        return SSHTransport(
            self.device["management_address"],
            os.getenv("NETWORK_USERNAME", "admin"),
            os.getenv("NETWORK_PASSWORD"),
            port=port,
        )

    async def identify(self):
        raw = await self._transport().run("show version")
        return {"vendor": "unknown", "data": raw, "raw": raw}

    async def get_facts(self):
        raw = await self._transport().run("show version")
        return {"vendor": "unknown", "data": raw, "raw": raw}

    async def get_interfaces(self):
        raise NotImplementedError("Unknown vendor: interface command must be supplied explicitly.")
