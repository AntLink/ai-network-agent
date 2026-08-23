from pydantic import BaseModel
from typing import List, Optional


class IpAddressCreate(BaseModel):
    address: str
    interface: str
    comment: Optional[str] = ""


class IpAddressDelete(BaseModel):
    address: str
    interface: str


class VlanCreate(BaseModel):
    name: str
    vlan_id: int
    interface: str
    comment: Optional[str] = ""


class VlanDelete(BaseModel):
    name: str


class BridgeCreate(BaseModel):
    name: str
    comment: Optional[str] = ""


class BridgePortCreate(BaseModel):
    bridge: str
    interface: str


class BridgePortDelete(BaseModel):
    bridge: str
    interface: str


class StaticRouteCreate(BaseModel):
    dst_address: str
    gateway: str
    distance: Optional[int] = 1
    comment: Optional[str] = ""


class StaticRouteDelete(BaseModel):
    dst_address: str
    gateway: str


class FirewallFilterCreate(BaseModel):
    chain: str
    action: str
    src_address: Optional[str] = None
    dst_address: Optional[str] = None
    protocol: Optional[str] = None
    dst_port: Optional[str] = None
    in_interface: Optional[str] = None
    out_interface: Optional[str] = None
    comment: Optional[str] = ""


class FirewallRuleDelete(BaseModel):
    rule_number: int


class FirewallNatCreate(BaseModel):
    chain: str
    action: str
    src_address: Optional[str] = None
    dst_address: Optional[str] = None
    protocol: Optional[str] = None
    dst_port: Optional[str] = None
    out_interface: Optional[str] = None
    to_addresses: Optional[str] = None
    to_ports: Optional[str] = None
    comment: Optional[str] = ""


class AddressListEntry(BaseModel):
    address: str
    list_name: str
    comment: Optional[str] = ""


class AddressListDelete(BaseModel):
    address: str
    list_name: str


class IpPoolCreate(BaseModel):
    name: str
    ranges: str
    comment: Optional[str] = ""


class IpPoolDelete(BaseModel):
    name: str


class DhcpServerCreate(BaseModel):
    name: str
    interface: str
    address_pool: str
    lease_time: Optional[str] = "10m"
    comment: Optional[str] = ""


class InterfaceSet(BaseModel):
    name: str
    mtu: Optional[int] = None
    disabled: Optional[bool] = None
    comment: Optional[str] = ""


class SystemIdentitySet(BaseModel):
    name: str


class SystemUserCreate(BaseModel):
    name: str
    password: str
    group: Optional[str] = "full"


class SystemUserDelete(BaseModel):
    name: str


class NtpClientSet(BaseModel):
    enabled: Optional[bool] = True
    primary_ntp: Optional[str] = ""
    secondary_ntp: Optional[str] = ""


class DnsSet(BaseModel):
    servers: str
    allow_remote_requests: Optional[bool] = True


class WirelessSecurityProfileCreate(BaseModel):
    name: str
    authentication_types: Optional[str] = "wpa2-psk"
    wpa2_psk: Optional[str] = ""
    comment: Optional[str] = ""


class CommandRunRequest(BaseModel):
    commands: List[str]


class MonitoringRequest(BaseModel):
    metrics: Optional[List[str]] = ["cpu", "memory", "disk", "temperature"]


# ---------------------------------------------------------------------------
# Hotspot
# ---------------------------------------------------------------------------

class HotspotServerCreate(BaseModel):
    name: str
    interface: str
    address_pool: Optional[str] = ""
    profile: Optional[str] = "default"
    comment: Optional[str] = ""


class HotspotNameDelete(BaseModel):
    name: str


class HotspotUserCreate(BaseModel):
    name: str
    password: Optional[str] = ""
    profile: Optional[str] = ""
    limit_uptime: Optional[str] = ""
    limit_bytes_total: Optional[str] = ""
    comment: Optional[str] = ""


class HotspotUserUpdate(BaseModel):
    name: str
    new_password: Optional[str] = None
    new_profile: Optional[str] = None
    limit_uptime: Optional[str] = None
    limit_bytes_total: Optional[str] = None
    comment: Optional[str] = None


class HotspotKickRequest(BaseModel):
    user: str


class HotspotUserProfileCreate(BaseModel):
    name: str
    rate_limit: Optional[str] = ""
    shared_users: Optional[str] = ""
    session_timeout: Optional[str] = ""
    address_pool: Optional[str] = ""
    comment: Optional[str] = ""


class HotspotIpBindingCreate(BaseModel):
    binding_type: str = "bypassed"
    mac_address: Optional[str] = ""
    address: Optional[str] = ""
    comment: Optional[str] = ""


class HotspotIpBindingDelete(BaseModel):
    mac_address: Optional[str] = ""
    address: Optional[str] = ""


# ---------------------------------------------------------------------------
# PPP / VPN tunnels (pptp, sstp, l2tp, ovpn, pppoe)
# ---------------------------------------------------------------------------

VALID_TUNNEL_TYPES = ["l2tp", "pptp", "sstp", "ovpn", "pppoe"]


class PppSecretCreate(BaseModel):
    name: str
    password: Optional[str] = ""
    service: Optional[str] = "any"
    profile: Optional[str] = "default"
    local_address: Optional[str] = ""
    remote_address: Optional[str] = ""
    comment: Optional[str] = ""


class PppSecretUpdate(BaseModel):
    name: str
    new_password: Optional[str] = None
    new_profile: Optional[str] = None
    new_remote_address: Optional[str] = None
    comment: Optional[str] = None


class PppNameRequest(BaseModel):
    name: str


class PppKickRequest(BaseModel):
    user: str


class TunnelServerSet(BaseModel):
    enabled: Optional[bool] = None
    use_ipsec: Optional[bool] = None
    ipsec_secret: Optional[str] = None
    default_profile: Optional[str] = None
    authentication: Optional[str] = None
    keepalive_timeout: Optional[int] = None


class TunnelClientCreate(BaseModel):
    tunnel_type: str
    name: str
    target: str
    user: str
    password: Optional[str] = ""
    profile: Optional[str] = ""
    use_ipsec: Optional[bool] = False
    ipsec_secret: Optional[str] = ""
    add_default_route: Optional[bool] = False
    comment: Optional[str] = ""


class TunnelClientRequest(BaseModel):
    tunnel_type: str
    name: str


class PppoeServerCreate(BaseModel):
    service_name: str
    interface: str
    default_profile: Optional[str] = "default-encryption"
    one_session_per_mac: Optional[bool] = True
    comment: Optional[str] = ""


class PppoeServerDelete(BaseModel):
    service_name: str
