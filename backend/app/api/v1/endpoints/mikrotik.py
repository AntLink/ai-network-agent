from fastapi import APIRouter, HTTPException
from app.services.device_service import device_service
from app.repositories.inventory import inventory_repository
from app.drivers.factory import get_driver
from app.schemas import mikrotik as schemas

router = APIRouter()


def _get_mikrotik_driver(device_id: str):
    device = inventory_repository.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    driver = get_driver(device)
    if driver.__class__.__name__ != "MikroTikDriver":
        raise HTTPException(status_code=400, detail=f"Device '{device_id}' is not a MikroTik device")
    return driver


# ---------------------------------------------------------------------------
# Read-only: resource dumps
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/ip-addresses")
async def get_ip_addresses(device_id: str):
    return await _get_mikrotik_driver(device_id).get_ip_addresses()


@router.get("/{device_id}/resources/pools")
async def get_ip_pool(device_id: str):
    return await _get_mikrotik_driver(device_id).get_ip_pool()


@router.get("/{device_id}/resources/dhcp-servers")
async def get_dhcp_server(device_id: str):
    return await _get_mikrotik_driver(device_id).get_dhcp_server()


@router.get("/{device_id}/resources/dhcp-leases")
async def get_dhcp_leases(device_id: str):
    return await _get_mikrotik_driver(device_id).get_dhcp_lease()


@router.get("/{device_id}/resources/bridges")
async def get_bridges(device_id: str):
    return await _get_mikrotik_driver(device_id).get_bridge()


@router.get("/{device_id}/resources/bridge-ports")
async def get_bridge_ports(device_id: str):
    return await _get_mikrotik_driver(device_id).get_bridge_ports()


@router.get("/{device_id}/resources/firewall/filter")
async def get_firewall_filter(device_id: str):
    return await _get_mikrotik_driver(device_id).get_firewall_filter()


@router.get("/{device_id}/resources/firewall/nat")
async def get_firewall_nat(device_id: str):
    return await _get_mikrotik_driver(device_id).get_firewall_nat()


@router.get("/{device_id}/resources/firewall/mangle")
async def get_firewall_mangle(device_id: str):
    return await _get_mikrotik_driver(device_id).get_firewall_mangle()


@router.get("/{device_id}/resources/firewall/address-lists")
async def get_firewall_address_list(device_id: str):
    return await _get_mikrotik_driver(device_id).get_firewall_address_list()


@router.get("/{device_id}/resources/ospf")
async def get_ospf(device_id: str):
    return await _get_mikrotik_driver(device_id).get_routing_ospf()


@router.get("/{device_id}/resources/bgp")
async def get_bgp(device_id: str):
    return await _get_mikrotik_driver(device_id).get_routing_bgp()


@router.get("/{device_id}/resources/static-routes")
async def get_static_routes(device_id: str):
    return await _get_mikrotik_driver(device_id).get_routing_static()


@router.get("/{device_id}/resources/ppp-secrets")
async def get_ppp_secrets(device_id: str):
    return await _get_mikrotik_driver(device_id).get_ppp_secret()


@router.get("/{device_id}/resources/ppp-profiles")
async def get_ppp_profiles(device_id: str):
    return await _get_mikrotik_driver(device_id).get_ppp_profile()


@router.get("/{device_id}/resources/wireless")
async def get_wireless(device_id: str):
    return await _get_mikrotik_driver(device_id).get_wireless()


@router.get("/{device_id}/resources/wireless-security-profiles")
async def get_wireless_security_profiles(device_id: str):
    return await _get_mikrotik_driver(device_id).get_wireless_security()


@router.get("/{device_id}/resources/snmp")
async def get_snmp(device_id: str):
    return await _get_mikrotik_driver(device_id).get_snmp()


@router.get("/{device_id}/resources/users")
async def get_system_users(device_id: str):
    return await _get_mikrotik_driver(device_id).get_system_users()


@router.get("/{device_id}/resources/logging")
async def get_system_logging(device_id: str):
    return await _get_mikrotik_driver(device_id).get_system_logging()


# ---------------------------------------------------------------------------
# IP address management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/ip-address")
async def add_ip_address(device_id: str, payload: schemas.IpAddressCreate):
    output = await _get_mikrotik_driver(device_id).add_ip_address(
        payload.address, payload.interface, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/ip-address")
async def remove_ip_address(device_id: str, payload: schemas.IpAddressDelete):
    output = await _get_mikrotik_driver(device_id).remove_ip_address(payload.address, payload.interface)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# VLAN management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/vlan")
async def add_vlan(device_id: str, payload: schemas.VlanCreate):
    output = await _get_mikrotik_driver(device_id).add_vlan(
        payload.name, payload.vlan_id, payload.interface, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/vlan")
async def remove_vlan(device_id: str, payload: schemas.VlanDelete):
    output = await _get_mikrotik_driver(device_id).remove_vlan(payload.name)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Bridge management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/bridge")
async def add_bridge(device_id: str, payload: schemas.BridgeCreate):
    output = await _get_mikrotik_driver(device_id).add_bridge(payload.name, payload.comment or "")
    return {"status": "applied", "output": output}


@router.post("/{device_id}/bridge/port")
async def add_bridge_port(device_id: str, payload: schemas.BridgePortCreate):
    output = await _get_mikrotik_driver(device_id).add_bridge_port(payload.bridge, payload.interface)
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/bridge/port")
async def remove_bridge_port(device_id: str, payload: schemas.BridgePortDelete):
    output = await _get_mikrotik_driver(device_id).remove_bridge_port(payload.bridge, payload.interface)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Static routing
# ---------------------------------------------------------------------------

@router.post("/{device_id}/static-route")
async def add_static_route(device_id: str, payload: schemas.StaticRouteCreate):
    output = await _get_mikrotik_driver(device_id).add_static_route(
        payload.dst_address, payload.gateway, payload.distance, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/static-route")
async def remove_static_route(device_id: str, payload: schemas.StaticRouteDelete):
    output = await _get_mikrotik_driver(device_id).remove_static_route(payload.dst_address, payload.gateway)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Firewall filter
# ---------------------------------------------------------------------------

@router.post("/{device_id}/firewall/filter")
async def add_firewall_filter(device_id: str, payload: schemas.FirewallFilterCreate):
    kwargs = {k: v for k, v in {
        "src-address": payload.src_address,
        "dst-address": payload.dst_address,
        "protocol": payload.protocol,
        "dst-port": payload.dst_port,
        "in-interface": payload.in_interface,
        "out-interface": payload.out_interface,
        "comment": f'"{payload.comment}"' if payload.comment else None,
    }.items() if v is not None}
    output = await _get_mikrotik_driver(device_id).add_firewall_filter(payload.chain, payload.action, **kwargs)
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/firewall/filter/{rule_number}")
async def remove_firewall_filter(device_id: str, rule_number: int):
    output = await _get_mikrotik_driver(device_id).remove_firewall_filter(rule_number)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Firewall NAT
# ---------------------------------------------------------------------------

@router.post("/{device_id}/firewall/nat")
async def add_firewall_nat(device_id: str, payload: schemas.FirewallNatCreate):
    kwargs = {k: v for k, v in {
        "src-address": payload.src_address,
        "dst-address": payload.dst_address,
        "protocol": payload.protocol,
        "dst-port": payload.dst_port,
        "out-interface": payload.out_interface,
        "to-addresses": payload.to_addresses,
        "to-ports": payload.to_ports,
        "comment": f'"{payload.comment}"' if payload.comment else None,
    }.items() if v is not None}
    output = await _get_mikrotik_driver(device_id).add_firewall_nat(payload.chain, payload.action, **kwargs)
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/firewall/nat/{rule_number}")
async def remove_firewall_nat(device_id: str, rule_number: int):
    output = await _get_mikrotik_driver(device_id).remove_firewall_nat(rule_number)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Firewall address-list
# ---------------------------------------------------------------------------

@router.post("/{device_id}/firewall/address-list")
async def add_address_list_entry(device_id: str, payload: schemas.AddressListEntry):
    output = await _get_mikrotik_driver(device_id).add_firewall_address_list(
        payload.address, payload.list_name, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/firewall/address-list")
async def remove_address_list_entry(device_id: str, payload: schemas.AddressListDelete):
    output = await _get_mikrotik_driver(device_id).remove_firewall_address_list(payload.address, payload.list_name)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# DHCP / IP pool
# ---------------------------------------------------------------------------

@router.post("/{device_id}/ip-pool")
async def add_ip_pool(device_id: str, payload: schemas.IpPoolCreate):
    output = await _get_mikrotik_driver(device_id).add_ip_pool(payload.name, payload.ranges, payload.comment or "")
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/ip-pool")
async def remove_ip_pool(device_id: str, payload: schemas.IpPoolDelete):
    output = await _get_mikrotik_driver(device_id).remove_ip_pool(payload.name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/dhcp-server")
async def add_dhcp_server(device_id: str, payload: schemas.DhcpServerCreate):
    output = await _get_mikrotik_driver(device_id).add_dhcp_server(
        payload.name, payload.interface, payload.address_pool, payload.lease_time, payload.comment or ""
    )
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Interface management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/interface/set")
async def set_interface(device_id: str, payload: schemas.InterfaceSet):
    kwargs = {}
    if payload.mtu is not None:
        kwargs["mtu"] = payload.mtu
    if payload.disabled is not None:
        kwargs["disabled"] = "yes" if payload.disabled else "no"
    if payload.comment:
        kwargs["comment"] = f'"{payload.comment}"'
    output = await _get_mikrotik_driver(device_id).set_interface(payload.name, **kwargs)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/interface/{name}/enable")
async def enable_interface(device_id: str, name: str):
    output = await _get_mikrotik_driver(device_id).enable_interface(name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/interface/{name}/disable")
async def disable_interface(device_id: str, name: str):
    output = await _get_mikrotik_driver(device_id).disable_interface(name)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# System management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/system/identity")
async def set_identity(device_id: str, payload: schemas.SystemIdentitySet):
    output = await _get_mikrotik_driver(device_id).set_system_identity(payload.name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/system/users")
async def add_system_user(device_id: str, payload: schemas.SystemUserCreate):
    output = await _get_mikrotik_driver(device_id).add_system_user(payload.name, payload.password, payload.group)
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/system/users/{name}")
async def remove_system_user(device_id: str, name: str):
    output = await _get_mikrotik_driver(device_id).remove_system_user(name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/system/ntp")
async def set_ntp_client(device_id: str, payload: schemas.NtpClientSet):
    output = await _get_mikrotik_driver(device_id).set_ntp_client(
        "yes" if payload.enabled else "no", payload.primary_ntp or "", payload.secondary_ntp or ""
    )
    return {"status": "applied", "output": output}


@router.post("/{device_id}/system/dns")
async def set_dns(device_id: str, payload: schemas.DnsSet):
    output = await _get_mikrotik_driver(device_id).set_dns(
        payload.servers, "yes" if payload.allow_remote_requests else "no"
    )
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Wireless
# ---------------------------------------------------------------------------

@router.post("/{device_id}/wireless/security-profile")
async def add_wireless_security_profile(device_id: str, payload: schemas.WirelessSecurityProfileCreate):
    output = await _get_mikrotik_driver(device_id).add_wireless_security_profile(
        payload.name, payload.authentication_types, payload.wpa2_psk or "", payload.comment or ""
    )
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Hotspot: read-only
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/hotspot/servers")
async def get_hotspot_servers(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_servers()


@router.get("/{device_id}/resources/hotspot/profiles")
async def get_hotspot_profiles(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_profiles()


@router.get("/{device_id}/resources/hotspot/users")
async def get_hotspot_users(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_users()


@router.get("/{device_id}/resources/hotspot/user-profiles")
async def get_hotspot_user_profiles(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_user_profiles()


@router.get("/{device_id}/resources/hotspot/active")
async def get_hotspot_active(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_active()


@router.get("/{device_id}/resources/hotspot/hosts")
async def get_hotspot_hosts(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_hosts()


@router.get("/{device_id}/resources/hotspot/ip-bindings")
async def get_hotspot_ip_bindings(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_ip_bindings()


@router.get("/{device_id}/resources/hotspot/walled-garden")
async def get_hotspot_walled_garden(device_id: str):
    return await _get_mikrotik_driver(device_id).get_hotspot_walled_garden()


# ---------------------------------------------------------------------------
# Hotspot: server management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/hotspot/server")
async def add_hotspot_server(device_id: str, payload: schemas.HotspotServerCreate):
    output = await _get_mikrotik_driver(device_id).add_hotspot_server(
        payload.name, payload.interface, payload.address_pool, payload.profile, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/hotspot/server")
async def remove_hotspot_server(device_id: str, payload: schemas.HotspotNameDelete):
    output = await _get_mikrotik_driver(device_id).remove_hotspot_server(payload.name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/hotspot/server/{name}/enable")
async def enable_hotspot_server(device_id: str, name: str):
    output = await _get_mikrotik_driver(device_id).enable_hotspot_server(name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/hotspot/server/{name}/disable")
async def disable_hotspot_server(device_id: str, name: str):
    output = await _get_mikrotik_driver(device_id).disable_hotspot_server(name)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Hotspot: user (voucher) management
# ---------------------------------------------------------------------------

@router.post("/{device_id}/hotspot/user")
async def add_hotspot_user(device_id: str, payload: schemas.HotspotUserCreate):
    output = await _get_mikrotik_driver(device_id).add_hotspot_user(
        payload.name, payload.password, payload.profile,
        payload.limit_uptime, payload.limit_bytes_total, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/hotspot/user")
async def remove_hotspot_user(device_id: str, payload: schemas.HotspotNameDelete):
    output = await _get_mikrotik_driver(device_id).remove_hotspot_user(payload.name)
    return {"status": "applied", "output": output}


@router.patch("/{device_id}/hotspot/user")
async def set_hotspot_user(device_id: str, payload: schemas.HotspotUserUpdate):
    kwargs = {k: v for k, v in {
        "password": payload.new_password,
        "profile": payload.new_profile,
        "limit-uptime": payload.limit_uptime,
        "limit-bytes-total": payload.limit_bytes_total,
        "comment": f'"{payload.comment}"' if payload.comment else None,
    }.items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")
    output = await _get_mikrotik_driver(device_id).set_hotspot_user(payload.name, **kwargs)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/hotspot/user/{name}/reset-counters")
async def reset_hotspot_user_counters(device_id: str, name: str):
    output = await _get_mikrotik_driver(device_id).reset_hotspot_user_counters(name)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/hotspot/reset-counters-all")
async def reset_all_hotspot_counters(device_id: str):
    output = await _get_mikrotik_driver(device_id).reset_all_hotspot_counters()
    return {"status": "applied", "output": output}


@router.post("/{device_id}/hotspot/kick")
async def kick_hotspot_user(device_id: str, payload: schemas.HotspotKickRequest):
    output = await _get_mikrotik_driver(device_id).kick_hotspot_user(payload.user)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Hotspot: user profiles
# ---------------------------------------------------------------------------

@router.post("/{device_id}/hotspot/user-profile")
async def add_hotspot_user_profile(device_id: str, payload: schemas.HotspotUserProfileCreate):
    output = await _get_mikrotik_driver(device_id).add_hotspot_user_profile(
        payload.name, payload.rate_limit, payload.shared_users,
        payload.session_timeout, payload.address_pool, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/hotspot/user-profile")
async def remove_hotspot_user_profile(device_id: str, payload: schemas.HotspotNameDelete):
    output = await _get_mikrotik_driver(device_id).remove_hotspot_user_profile(payload.name)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# Hotspot: IP binding
# ---------------------------------------------------------------------------

@router.post("/{device_id}/hotspot/ip-binding")
async def add_hotspot_ip_binding(device_id: str, payload: schemas.HotspotIpBindingCreate):
    if not payload.mac_address and not payload.address:
        raise HTTPException(status_code=400, detail="mac_address or address is required")
    output = await _get_mikrotik_driver(device_id).add_hotspot_ip_binding(
        payload.binding_type, payload.mac_address or "", payload.address or "", payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/hotspot/ip-binding")
async def remove_hotspot_ip_binding(device_id: str, payload: schemas.HotspotIpBindingDelete):
    if not payload.mac_address and not payload.address:
        raise HTTPException(status_code=400, detail="mac_address or address is required")
    output = await _get_mikrotik_driver(device_id).remove_hotspot_ip_binding(
        payload.mac_address or "", payload.address or ""
    )
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# PPP family: secrets, profiles, active
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/ppp-active")
async def get_ppp_active(device_id: str):
    return await _get_mikrotik_driver(device_id).get_ppp_active()


@router.post("/{device_id}/ppp/secret")
async def add_ppp_secret(device_id: str, payload: schemas.PppSecretCreate):
    output = await _get_mikrotik_driver(device_id).add_ppp_secret(
        payload.name, payload.password, payload.service, payload.profile,
        payload.local_address, payload.remote_address, payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/ppp/secret")
async def remove_ppp_secret(device_id: str, payload: schemas.PppNameRequest):
    output = await _get_mikrotik_driver(device_id).remove_ppp_secret(payload.name)
    return {"status": "applied", "output": output}


@router.patch("/{device_id}/ppp/secret")
async def set_ppp_secret(device_id: str, payload: schemas.PppSecretUpdate):
    kwargs = {k: v for k, v in {
        "password": payload.new_password,
        "profile": payload.new_profile,
        "remote-address": payload.new_remote_address,
        "comment": f'"{payload.comment}"' if payload.comment else None,
    }.items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")
    output = await _get_mikrotik_driver(device_id).set_ppp_secret(payload.name, **kwargs)
    return {"status": "applied", "output": output}


@router.post("/{device_id}/ppp/kick")
async def kick_ppp_session(device_id: str, payload: schemas.PppKickRequest):
    try:
        output = await _get_mikrotik_driver(device_id).kick_ppp_session(payload.user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# VPN tunnel servers (pptp / sstp / l2tp / ovpn)
# ---------------------------------------------------------------------------

def _validate_tunnel_type(tunnel_type: str) -> str:
    if tunnel_type not in schemas.VALID_TUNNEL_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid tunnel type '{tunnel_type}'. Allowed: {', '.join(schemas.VALID_TUNNEL_TYPES)}")
    return tunnel_type


@router.get("/{device_id}/resources/tunnel/{tunnel_type}/server")
async def get_tunnel_server_status(device_id: str, tunnel_type: str):
    _validate_tunnel_type(tunnel_type)
    try:
        return await _get_mikrotik_driver(device_id).get_tunnel_server_status(tunnel_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{device_id}/tunnel/{tunnel_type}/server")
async def set_tunnel_server(device_id: str, tunnel_type: str, payload: schemas.TunnelServerSet):
    _validate_tunnel_type(tunnel_type)
    kwargs = {}
    if payload.use_ipsec is not None:
        kwargs["use-ipsec"] = "yes" if payload.use_ipsec else "no"
    if payload.ipsec_secret is not None and payload.ipsec_secret != "":
        kwargs["ipsec-secret"] = payload.ipsec_secret
    if payload.default_profile:
        kwargs["default-profile"] = payload.default_profile
    if payload.authentication:
        kwargs["authentication"] = payload.authentication
    if payload.keepalive_timeout is not None:
        kwargs["keepalive-timeout"] = payload.keepalive_timeout
    try:
        output = await _get_mikrotik_driver(device_id).set_tunnel_server(
            tunnel_type, enabled=payload.enabled, **kwargs
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "applied", "output": output}


@router.get("/{device_id}/resources/pppoe-servers")
async def get_pppoe_servers(device_id: str):
    return await _get_mikrotik_driver(device_id).get_pppoe_servers()


@router.post("/{device_id}/pppoe/server-instance")
async def add_pppoe_server_instance(device_id: str, payload: schemas.PppoeServerCreate):
    output = await _get_mikrotik_driver(device_id).add_pppoe_server(
        payload.service_name, payload.interface, payload.default_profile,
        "yes" if payload.one_session_per_mac else "no", payload.comment or ""
    )
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/pppoe/server-instance")
async def remove_pppoe_server_instance(device_id: str, payload: schemas.PppoeServerDelete):
    output = await _get_mikrotik_driver(device_id).remove_pppoe_server(payload.service_name)
    return {"status": "applied", "output": output}


# ---------------------------------------------------------------------------
# VPN tunnel clients (l2tp / pptp / sstp / ovpn / pppoe)
# ---------------------------------------------------------------------------

@router.get("/{device_id}/resources/tunnel/{tunnel_type}/clients")
async def get_tunnel_clients(device_id: str, tunnel_type: str):
    _validate_tunnel_type(tunnel_type)
    try:
        return await _get_mikrotik_driver(device_id).get_tunnel_clients(tunnel_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{device_id}/tunnel/client")
async def add_tunnel_client(device_id: str, payload: schemas.TunnelClientCreate):
    _validate_tunnel_type(payload.tunnel_type)
    try:
        output = await _get_mikrotik_driver(device_id).add_tunnel_client(
            payload.tunnel_type, payload.name, payload.target, payload.user,
            payload.password or "", payload.profile or "",
            bool(payload.use_ipsec), payload.ipsec_secret or "",
            bool(payload.add_default_route), payload.comment or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "applied", "output": output}


@router.delete("/{device_id}/tunnel/client")
async def remove_tunnel_client(device_id: str, payload: schemas.TunnelClientRequest):
    _validate_tunnel_type(payload.tunnel_type)
    try:
        output = await _get_mikrotik_driver(device_id).remove_tunnel_client(
            payload.tunnel_type, payload.name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "applied", "output": output}


@router.post("/{device_id}/tunnel/{tunnel_type}/client/{name}/{action}")
async def manage_tunnel_client(device_id: str, tunnel_type: str, name: str, action: str):
    _validate_tunnel_type(tunnel_type)
    driver = _get_mikrotik_driver(device_id)
    try:
        if action == "enable":
            output = await driver.set_tunnel_client_state(tunnel_type, name, True)
        elif action == "disable":
            output = await driver.set_tunnel_client_state(tunnel_type, name, False)
        elif action == "monitor":
            output = await driver.monitor_tunnel_client(tunnel_type, name)
        else:
            raise HTTPException(status_code=400, detail="action must be enable|disable|monitor")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "applied" if action != "monitor" else "ok", "output": output}


# ---------------------------------------------------------------------------
# Raw commands + monitoring
# ---------------------------------------------------------------------------

@router.post("/{device_id}/commands/run")
async def run_commands(device_id: str, payload: schemas.CommandRunRequest):
    driver = _get_mikrotik_driver(device_id)
    result = await driver.apply(payload.commands)
    return {"status": "applied", **result}


@router.post("/{device_id}/monitoring")
async def get_monitoring(device_id: str, payload: schemas.MonitoringRequest):
    output = await _get_mikrotik_driver(device_id).get_monitoring(payload.metrics)
    return {"status": "ok", "metrics": output}
