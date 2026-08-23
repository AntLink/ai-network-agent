from abc import ABC, abstractmethod

class BaseDriver(ABC):
    def __init__(self, device: dict):
        self.device = device

    @abstractmethod
    async def identify(self): ...

    @abstractmethod
    async def get_facts(self): ...

    @abstractmethod
    async def get_interfaces(self): ...

    async def get_routes(self):
        raise NotImplementedError

    async def get_config(self):
        raise NotImplementedError

    async def get_vlans(self):
        raise NotImplementedError

    async def backup(self):
        raise NotImplementedError

    async def apply(self, commands: list[str]):
        raise NotImplementedError
