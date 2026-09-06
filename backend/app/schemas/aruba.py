"""Request schemas for the Aruba AOS-CX REST endpoints."""
from typing import List, Optional

from pydantic import BaseModel


class InterfaceDescriptionSet(BaseModel):
    interface: str
    description: str


class InterfaceAddressSet(BaseModel):
    interface: str
    address: str


class InterfaceStateSet(BaseModel):
    interface: str
    action: str


class InterfaceTarget(BaseModel):
    interface: str


class StaticRouteCreate(BaseModel):
    prefix: str
    gateway: str
    distance: Optional[int] = None


class StaticRouteDelete(BaseModel):
    prefix: str
    gateway: str


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


class CommandRunRequest(BaseModel):
    command: str


class PingRequest(BaseModel):
    address: str
    repeat: Optional[int] = 3
    timeout: Optional[int] = 2


class TracerouteRequest(BaseModel):
    address: str
    timeout: Optional[int] = 2
    probes: Optional[int] = 2