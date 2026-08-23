import os
from app.drivers.base import BaseDriver
from app.transports.ssh import SSHTransport

class GenericSSHDriver(BaseDriver):
    def _transport(self):
        return SSHTransport(
            self.device["management_address"],
            os.getenv("NETWORK_USERNAME", "admin"),
            os.getenv("NETWORK_PASSWORD"),
        )

    async def identify(self):
        return {"vendor": "unknown", "raw": await self._transport().run("show version")}

    async def get_facts(self):
        return await self.identify()

    async def get_interfaces(self):
        raise NotImplementedError("Unknown vendor: interface command must be supplied explicitly.")
