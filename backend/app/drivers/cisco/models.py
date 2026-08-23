"""Pydantic models for Cisco IOS configuration."""
from pydantic import BaseModel, Field
from typing import Optional, List


class Interface(BaseModel):
    """Interface configuration model."""
    name: str = Field(..., description="Interface name, e.g. GigabitEthernet0/1")
    ip_address: Optional[str] = Field(None, description="IPv4 address")
    subnet_mask: Optional[str] = Field(None, description="Subnet mask")
    description: Optional[str] = Field("", description="Interface description")
    is_enabled: bool = Field(True, description="no shutdown / shutdown (administrative)")
    is_up: Optional[bool] = Field(None, description="Line protocol up (read-only dari show)")
    mtu: Optional[int] = Field(None, description="MTU size")

    def to_config_commands(self) -> List[str]:
        """Generate Cisco IOS configuration commands."""
        cmds = [f"interface {self.name}"]
        if self.description:
            cmds.append(f" description {self.description}")
        if self.ip_address and self.subnet_mask:
            cmds.append(f" ip address {self.ip_address} {self.subnet_mask}")
        if not self.is_enabled:
            cmds.append(" shutdown")
        else:
            cmds.append(" no shutdown")
        if self.mtu:
            cmds.append(f" mtu {self.mtu}")
        cmds.append("exit")
        return cmds


class StaticRoute(BaseModel):
    """Static route model."""
    destination: str = Field(..., description="Destination network")
    mask: str = Field(..., description="Subnet mask")
    next_hop: str = Field(..., description="Next-hop IP address")
    distance: Optional[int] = Field(1, description="Administrative distance")

    def to_config_commands(self) -> List[str]:
        cmd = f"ip route {self.destination} {self.mask} {self.next_hop}"
        if self.distance and self.distance != 1:
            cmd += f" {self.distance}"
        return [cmd]


class OSPFNetwork(BaseModel):
    """OSPF network statement."""
    network: str = Field(..., description="Network address")
    wildcard: str = Field(..., description="Wildcard mask")
    area: int = Field(0, description="OSPF area")


class OSPFConfig(BaseModel):
    """OSPF process configuration."""
    process_id: int = Field(..., description="OSPF process ID")
    router_id: Optional[str] = Field(None, description="Router ID")
    networks: List[OSPFNetwork] = Field(default_factory=list)

    def to_config_commands(self) -> List[str]:
        cmds = [f"router ospf {self.process_id}"]
        if self.router_id:
            cmds.append(f" router-id {self.router_id}")
        for net in self.networks:
            cmds.append(f" network {net.network} {net.wildcard} area {net.area}")
        cmds.append("exit")
        return cmds