from pydantic import BaseModel
from typing import List, Optional


class DnsSet(BaseModel):
    servers: List[str]


class NtpServerAdd(BaseModel):
    server: str


class NtpServerRemove(BaseModel):
    server: str


class BannerSet(BaseModel):
    text: str


class LocalUserCreate(BaseModel):
    username: str
    password: str
    privilege: Optional[int] = 1


class LocalUserDelete(BaseModel):
    username: str


class InterfaceDescriptionSet(BaseModel):
    interface: str
    description: str


class InterfaceAddressSet(BaseModel):
    interface: str
    address: str


class InterfaceMtuSet(BaseModel):
    interface: str
    mtu: int


class InterfaceStateSet(BaseModel):
    interface: str


class StaticRouteCreate(BaseModel):
    prefix: str
    gateway: str
    distance: Optional[int] = None


class StaticRouteDelete(BaseModel):
    prefix: str
    gateway: str


class AclCreate(BaseModel):
    name: str
    acl_type: str
    rules: List[str]


class AclDelete(BaseModel):
    name: str
    acl_type: str


class AclApply(BaseModel):
    name: str
    interface: str
    direction: str


class CommandRunRequest(BaseModel):
    commands: List[str]


class PingRequest(BaseModel):
    address: str
    repeat: Optional[int] = 3
    timeout: Optional[int] = 2


class TracerouteRequest(BaseModel):
    address: str
    timeout: Optional[int] = 2
    probes: Optional[int] = 2


class VerifyCheck(BaseModel):
    command: str
    expect: Optional[str] = None


class ConfigTransaction(BaseModel):
    commands: List[str]
    verify: List[VerifyCheck] = []
    save_on_success: bool = False
    description: Optional[str] = ""


class NetmikoConfigPush(BaseModel):
    commands: List[str]
    save: bool = True


# ---------------------------------------------------------------------------
# Layer-2 (VLAN / access / trunk / subinterface / SVI)
# ---------------------------------------------------------------------------

class VlanCreate(BaseModel):
    vlan_id: int
    name: Optional[str] = None


class VlanDelete(BaseModel):
    vlan_id: int


class AccessPortSet(BaseModel):
    interface: str
    vlan_id: int


class TrunkPortSet(BaseModel):
    interface: str
    allowed_vlans: str = "all"


class SubinterfaceCreate(BaseModel):
    parent_interface: str
    sub_id: int
    vlan_id: int
    ip_address: Optional[str] = None


class SviSet(BaseModel):
    vlan_id: int
    ip_address: Optional[str] = None
    shutdown: bool = False
