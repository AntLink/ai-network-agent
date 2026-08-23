from pydantic import BaseModel
from typing import Literal, Optional

class DeviceCreate(BaseModel):
    id: str
    hostname: Optional[str] = None
    management_address: str
    vendor: Optional[str] = None
    platform: Optional[str] = None
    transport: Literal["ssh", "rest", "netconf", "console"] = "ssh"
    console_host: Optional[str] = None
    console_port: Optional[int] = None

class DeviceRead(DeviceCreate):
    status: str = "active"
