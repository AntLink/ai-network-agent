import os
import time
from pathlib import Path
from dotenv import load_dotenv
from app.drivers.base import BaseDriver
from app.transports.ssh import SSHTransport
from app.core.audit import log_event
from .parser import MikroTikParser

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class MikroTikDriver(BaseDriver):
    def _transport(self):
        prefix = self.device["id"].upper().replace("-", "_")
        username = os.getenv(f"{prefix}_USERNAME", os.getenv("NETWORK_USERNAME", "admin"))
        password = os.getenv(f"{prefix}_PASSWORD", os.getenv("NETWORK_PASSWORD"))
        return SSHTransport(self.device["management_address"], username, password)

    async def _logged(self, action: str, detail: str, fn):
        """Run an operation with timed OK/FAIL audit logging (parity with Cisco)."""
        device_id = self.device["id"]
        t0 = time.perf_counter()
        try:
            out = await fn()
            duration = round((time.perf_counter() - t0) * 1000)
            log_event(device_id, action, detail, status="OK", duration_ms=duration)
            return out
        except Exception as e:
            duration = round((time.perf_counter() - t0) * 1000)
            log_event(device_id, action, detail, status="FAIL", duration_ms=duration, error=str(e))
            raise

    async def identify(self):
        t = self._transport()
        log_event(self.device["id"], "identify", "/system identity print")
        identity_raw = await t.run("/system identity print")
        log_event(self.device["id"], "identify", "/system resource print")
        resource_raw = await t.run("/system resource print")
        identity_parsed = MikroTikParser.parse_identity(identity_raw)
        resource_parsed = MikroTikParser.parse_resource(resource_raw)
        return {
            "vendor": "mikrotik", 
            "identity": {"data": identity_parsed, "raw": identity_raw},
            "resource": {"data": resource_parsed, "raw": resource_raw}
        }

    async def get_facts(self):
        cmd = "/system resource print"
        log_event(self.device["id"], "get_facts", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_resource(raw)
        return {"data": parsed, "raw": raw}

    async def get_interfaces(self):
        cmd = "/interface print detail without-paging"
        log_event(self.device["id"], "get_interfaces", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_interfaces(raw)
        return {"data": parsed, "raw": raw}

    async def get_routes(self):
        cmd = "/ip route print detail without-paging"
        log_event(self.device["id"], "get_routes", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_routes(raw)
        return {"data": parsed, "raw": raw}

    async def get_config(self):
        cmd = "/export terse"
        log_event(self.device["id"], "get_config", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_config(raw)
        return {"data": parsed, "raw": raw}

    async def get_vlans(self):
        cmd = "/interface vlan print detail without-paging"
        log_event(self.device["id"], "get_vlans", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_bridge(self):
        cmd = "/interface bridge print detail without-paging"
        log_event(self.device["id"], "get_bridge", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_bridge_ports(self):
        cmd = "/interface bridge port print detail without-paging"
        log_event(self.device["id"], "get_bridge_ports", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_ip_addresses(self):
        cmd = "/ip address print detail without-paging"
        log_event(self.device["id"], "get_ip_addresses", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_ip_addresses(raw)
        return {"data": parsed, "raw": raw}

    async def get_ip_pool(self):
        cmd = "/ip pool print detail without-paging"
        log_event(self.device["id"], "get_ip_pool", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_dhcp_server(self):
        cmd = "/ip dhcp-server print detail without-paging"
        log_event(self.device["id"], "get_dhcp_server", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_dhcp_server(raw)
        return {"data": parsed, "raw": raw}

    async def get_dhcp_lease(self):
        cmd = "/ip dhcp-server lease print detail without-paging"
        log_event(self.device["id"], "get_dhcp_lease", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_firewall_filter(self):
        cmd = "/ip firewall filter print detail without-paging"
        log_event(self.device["id"], "get_firewall_filter", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_firewall_nat(self):
        cmd = "/ip firewall nat print detail without-paging"
        log_event(self.device["id"], "get_firewall_nat", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_firewall_mangle(self):
        cmd = "/ip firewall mangle print detail without-paging"
        log_event(self.device["id"], "get_firewall_mangle", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_firewall_address_list(self):
        cmd = "/ip firewall address-list print detail without-paging"
        log_event(self.device["id"], "get_firewall_address_list", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_routing_ospf(self):
        cmd = "/routing ospf instance print detail without-paging"
        log_event(self.device["id"], "get_routing_ospf", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_routing_bgp(self):
        cmd = "/routing bgp instance print detail without-paging"
        log_event(self.device["id"], "get_routing_bgp", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_routing_static(self):
        cmd = "/ip route print detail without-paging where static"
        log_event(self.device["id"], "get_routing_static", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_ppp_secret(self):
        cmd = "/ppp secret print detail without-paging"
        log_event(self.device["id"], "get_ppp_secret", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_ppp_profile(self):
        cmd = "/ppp profile print detail without-paging"
        log_event(self.device["id"], "get_ppp_profile", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_wireless(self):
        cmd = "/interface wireless print detail without-paging"
        log_event(self.device["id"], "get_wireless", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_wireless_security(self):
        cmd = "/interface wireless security-profiles print detail without-paging"
        log_event(self.device["id"], "get_wireless_security", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_snmp(self):
        cmd = "/snmp print detail without-paging"
        log_event(self.device["id"], "get_snmp", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_resource(raw), "raw": raw}

    async def get_ntp(self):
        cmd = "/system ntp client print detail without-paging"
        log_event(self.device["id"], "get_ntp", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_resource(raw), "raw": raw}

    async def get_dns(self):
        cmd = "/ip dns print detail without-paging"
        log_event(self.device["id"], "get_dns", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_resource(raw), "raw": raw}

    async def get_system_users(self):
        cmd = "/user print detail without-paging"
        log_event(self.device["id"], "get_system_users", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_system_users(raw)
        return {"data": parsed, "raw": raw}

    async def get_system_logging(self):
        cmd = "/system logging print detail without-paging"
        log_event(self.device["id"], "get_system_logging", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def backup(self):
        cmd = "/export terse"
        log_event(self.device["id"], "backup", cmd)
        raw = await self._transport().run(cmd)
        parsed = MikroTikParser.parse_config(raw)
        return {"data": parsed, "raw": raw}

    async def apply(self, commands: list[str]):
        t = self._transport()
        outputs = []
        for command in commands:
            log_event(self.device["id"], "apply", command)
            outputs.append(await t.run(command))
        return {"success": True, "outputs": outputs}

    # Configuration Methods (for plan/apply workflow)
    async def add_ip_address(self, address: str, interface: str, comment: str = ""):
        cmd = f'/ip address add address={address} interface={interface}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ip_address", cmd)
        return await self._transport().run(cmd)

    async def remove_ip_address(self, address: str, interface: str):
        cmd = f'/ip address remove [find address={address} interface={interface}]'
        log_event(self.device["id"], "remove_ip_address", cmd)
        return await self._transport().run(cmd)

    async def add_vlan(self, name: str, vlan_id: int, interface: str, comment: str = ""):
        cmd = f'/interface vlan add name={name} vlan-id={vlan_id} interface={interface}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_vlan", cmd)
        return await self._transport().run(cmd)

    async def remove_vlan(self, name: str):
        cmd = f'/interface vlan remove [find name={name}]'
        log_event(self.device["id"], "remove_vlan", cmd)
        return await self._transport().run(cmd)

    async def add_bridge(self, name: str, comment: str = ""):
        cmd = f'/interface bridge add name={name}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_bridge", cmd)
        return await self._transport().run(cmd)

    async def add_bridge_port(self, bridge: str, interface: str):
        cmd = f'/interface bridge port add bridge={bridge} interface={interface}'
        log_event(self.device["id"], "add_bridge_port", cmd)
        return await self._transport().run(cmd)

    async def remove_bridge_port(self, bridge: str, interface: str):
        cmd = f'/interface bridge port remove [find bridge={bridge} interface={interface}]'
        log_event(self.device["id"], "remove_bridge_port", cmd)
        return await self._transport().run(cmd)

    async def add_firewall_filter(self, chain: str, action: str, **kwargs):
        parts = [f'/ip firewall filter add chain={chain} action={action}']
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f'{key}={value}')
        cmd = ' '.join(parts)
        log_event(self.device["id"], "add_firewall_filter", cmd)
        return await self._transport().run(cmd)

    async def remove_firewall_filter(self, rule_number: int):
        cmd = f'/ip firewall filter remove numbers={rule_number}'
        log_event(self.device["id"], "remove_firewall_filter", cmd)
        return await self._transport().run(cmd)

    async def add_firewall_nat(self, chain: str, action: str, **kwargs):
        parts = [f'/ip firewall nat add chain={chain} action={action}']
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f'{key}={value}')
        cmd = ' '.join(parts)
        log_event(self.device["id"], "add_firewall_nat", cmd)
        return await self._transport().run(cmd)

    async def remove_firewall_nat(self, rule_number: int):
        cmd = f'/ip firewall nat remove numbers={rule_number}'
        log_event(self.device["id"], "remove_firewall_nat", cmd)
        return await self._transport().run(cmd)

    async def add_firewall_address_list(self, address: str, list_name: str, comment: str = ""):
        cmd = f'/ip firewall address-list add address={address} list={list_name}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_firewall_address_list", cmd)
        return await self._transport().run(cmd)

    async def remove_firewall_address_list(self, address: str, list_name: str):
        cmd = f'/ip firewall address-list remove [find address={address} list={list_name}]'
        log_event(self.device["id"], "remove_firewall_address_list", cmd)
        return await self._transport().run(cmd)

    async def add_static_route(self, dst_address: str, gateway: str, distance: int = 1, comment: str = ""):
        cmd = f'/ip route add dst-address={dst_address} gateway={gateway} distance={distance}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_static_route", cmd)
        return await self._transport().run(cmd)

    async def remove_static_route(self, dst_address: str, gateway: str):
        cmd = f'/ip route remove [find dst-address={dst_address} gateway={gateway}]'
        log_event(self.device["id"], "remove_static_route", cmd)
        return await self._transport().run(cmd)

    async def add_dhcp_server(self, name: str, interface: str, address_pool: str, lease_time: str = "10m", comment: str = ""):
        cmd = f'/ip dhcp-server add name={name} interface={interface} address-pool={address_pool} lease-time={lease_time}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_dhcp_server", cmd)
        return await self._transport().run(cmd)

    async def add_ip_pool(self, name: str, ranges: str, comment: str = ""):
        cmd = f'/ip pool add name={name} ranges={ranges}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ip_pool", cmd)
        return await self._transport().run(cmd)

    async def remove_ip_pool(self, name: str):
        cmd = f'/ip pool remove [find name={name}]'
        log_event(self.device["id"], "remove_ip_pool", cmd)
        return await self._transport().run(cmd)

    async def set_interface(self, name: str, **kwargs):
        parts = [f'/interface set [find name={name}]']
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f'{key}={value}')
        cmd = ' '.join(parts)
        log_event(self.device["id"], "set_interface", cmd)
        return await self._transport().run(cmd)

    async def enable_interface(self, name: str):
        cmd = f'/interface enable [find name={name}]'
        log_event(self.device["id"], "enable_interface", cmd)
        return await self._transport().run(cmd)

    async def disable_interface(self, name: str):
        cmd = f'/interface disable [find name={name}]'
        log_event(self.device["id"], "disable_interface", cmd)
        return await self._transport().run(cmd)

    async def set_system_identity(self, name: str):
        cmd = f'/system identity set name="{name}"'
        log_event(self.device["id"], "set_system_identity", cmd)
        return await self._transport().run(cmd)

    async def add_system_user(self, name: str, password: str, group: str = "full"):
        cmd = f'/user add name={name} password={password} group={group}'
        log_event(self.device["id"], "add_system_user", cmd)
        return await self._transport().run(cmd)

    async def remove_system_user(self, name: str):
        cmd = f'/user remove [find name={name}]'
        log_event(self.device["id"], "remove_system_user", cmd)
        return await self._transport().run(cmd)

    async def set_ntp_client(self, enabled: str = "yes", primary_ntp: str = "", secondary_ntp: str = ""):
        cmd = f'/system ntp client set enabled={enabled}'
        if primary_ntp:
            cmd += f' primary-ntp={primary_ntp}'
        if secondary_ntp:
            cmd += f' secondary-ntp={secondary_ntp}'
        log_event(self.device["id"], "set_ntp_client", cmd)
        return await self._transport().run(cmd)

    async def set_dns(self, servers: str, allow_remote_requests: str = "yes"):
        cmd = f'/ip dns set servers={servers} allow-remote-requests={allow_remote_requests}'
        log_event(self.device["id"], "set_dns", cmd)
        return await self._transport().run(cmd)

    async def add_wireless_security_profile(self, name: str, authentication_types: str = "wpa2-psk", wpa2_psk: str = "", comment: str = ""):
        cmd = f'/interface wireless security-profiles add name={name} authentication-types={authentication_types}'
        if wpa2_psk:
            cmd += f' wpa2-pre-shared-key={wpa2_psk}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_wireless_security_profile", cmd)
        return await self._transport().run(cmd)

    async def get_monitoring(self, metrics: list[str] = None):
        t = self._transport()
        outputs = {}
        if metrics is None:
            metrics = ["cpu", "memory", "disk", "temperature", "voltage"]

        if "cpu" in metrics:
            log_event(self.device["id"], "monitoring", "/system resource cpu print")
            outputs["cpu"] = await t.run("/system resource cpu print")
        if "memory" in metrics:
            log_event(self.device["id"], "monitoring", "/system resource print")
            outputs["memory"] = await t.run("/system resource print")
        if "disk" in metrics:
            log_event(self.device["id"], "monitoring", "/system disk print")
            outputs["disk"] = await t.run("/system disk print")
        if "temperature" in metrics:
            log_event(self.device["id"], "monitoring", "/system health print")
            outputs["health"] = await t.run("/system health print")
        if "voltage" in metrics:
            log_event(self.device["id"], "monitoring", "/system health print")
            outputs["health"] = await t.run("/system health print")

        return outputs

    # ------------------------------------------------------------------
    # Hotspot: read-only
    # ------------------------------------------------------------------

    async def get_hotspot_servers(self):
        cmd = "/ip hotspot print detail without-paging"
        log_event(self.device["id"], "get_hotspot_servers", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_profiles(self):
        cmd = "/ip hotspot profile print detail without-paging"
        log_event(self.device["id"], "get_hotspot_profiles", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_users(self):
        cmd = "/ip hotspot user print detail without-paging"
        log_event(self.device["id"], "get_hotspot_users", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_user_profiles(self):
        cmd = "/ip hotspot user profile print detail without-paging"
        log_event(self.device["id"], "get_hotspot_user_profiles", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_active(self):
        cmd = "/ip hotspot active print detail without-paging"
        log_event(self.device["id"], "get_hotspot_active", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_hosts(self):
        cmd = "/ip hotspot host print detail without-paging"
        log_event(self.device["id"], "get_hotspot_hosts", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_ip_bindings(self):
        cmd = "/ip hotspot ip-binding print detail without-paging"
        log_event(self.device["id"], "get_hotspot_ip_bindings", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def get_hotspot_walled_garden(self):
        cmd = "/ip hotspot walled-garden print detail without-paging"
        log_event(self.device["id"], "get_hotspot_walled_garden", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    # ------------------------------------------------------------------
    # Hotspot: server management
    # ------------------------------------------------------------------

    async def add_hotspot_server(self, name: str, interface: str, address_pool: str = "", profile: str = "default", comment: str = ""):
        cmd = f'/ip hotspot add name={name} interface={interface} profile={profile}'
        if address_pool:
            cmd += f' address-pool={address_pool}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_hotspot_server", cmd)
        return await self._transport().run(cmd)

    async def remove_hotspot_server(self, name: str):
        cmd = f'/ip hotspot remove [find name={name}]'
        log_event(self.device["id"], "remove_hotspot_server", cmd)
        return await self._transport().run(cmd)

    async def enable_hotspot_server(self, name: str):
        cmd = f'/ip hotspot enable [find name={name}]'
        log_event(self.device["id"], "enable_hotspot_server", cmd)
        return await self._transport().run(cmd)

    async def disable_hotspot_server(self, name: str):
        cmd = f'/ip hotspot disable [find name={name}]'
        log_event(self.device["id"], "disable_hotspot_server", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # Hotspot: user (voucher) management
    # ------------------------------------------------------------------

    async def add_hotspot_user(self, name: str, password: str = "", profile: str = "", limit_uptime: str = "", limit_bytes_total: str = "", comment: str = ""):
        cmd = f'/ip hotspot user add name={name}'
        if password:
            cmd += f' password={password}'
        if profile:
            cmd += f' profile={profile}'
        if limit_uptime:
            cmd += f' limit-uptime={limit_uptime}'
        if limit_bytes_total:
            cmd += f' limit-bytes-total={limit_bytes_total}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_hotspot_user", cmd)
        return await self._transport().run(cmd)

    async def remove_hotspot_user(self, name: str):
        cmd = f'/ip hotspot user remove [find name={name}]'
        log_event(self.device["id"], "remove_hotspot_user", cmd)
        return await self._transport().run(cmd)

    async def set_hotspot_user(self, name: str, **kwargs):
        parts = [f'/ip hotspot user set [find name={name}]']
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f'{key}={value}')
        cmd = ' '.join(parts)
        log_event(self.device["id"], "set_hotspot_user", cmd)
        return await self._transport().run(cmd)

    async def reset_hotspot_user_counters(self, name: str):
        cmd = f'/ip hotspot user reset-counters [find name={name}]'
        log_event(self.device["id"], "reset_hotspot_user_counters", cmd)
        return await self._transport().run(cmd)

    async def reset_all_hotspot_counters(self):
        cmd = '/ip hotspot user reset-counters-all'
        log_event(self.device["id"], "reset_all_hotspot_counters", cmd)
        return await self._transport().run(cmd)

    async def kick_hotspot_user(self, user: str):
        cmd = f'/ip hotspot active remove [find user={user}]'
        log_event(self.device["id"], "kick_hotspot_user", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # Hotspot: user profiles
    # ------------------------------------------------------------------

    async def add_hotspot_user_profile(self, name: str, rate_limit: str = "", shared_users: str = "", session_timeout: str = "", address_pool: str = "", comment: str = ""):
        cmd = f'/ip hotspot user profile add name={name}'
        if rate_limit:
            cmd += f' rate-limit={rate_limit}'
        if shared_users:
            cmd += f' shared-users={shared_users}'
        if session_timeout:
            cmd += f' session-timeout={session_timeout}'
        if address_pool:
            cmd += f' address-pool={address_pool}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_hotspot_user_profile", cmd)
        return await self._transport().run(cmd)

    async def remove_hotspot_user_profile(self, name: str):
        cmd = f'/ip hotspot user profile remove [find name={name}]'
        log_event(self.device["id"], "remove_hotspot_user_profile", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # Hotspot: IP binding
    # ------------------------------------------------------------------

    async def add_hotspot_ip_binding(self, binding_type: str, mac_address: str = "", address: str = "", comment: str = ""):
        cmd = f'/ip hotspot ip-binding add type={binding_type}'
        if mac_address:
            cmd += f' mac-address={mac_address}'
        if address:
            cmd += f' address={address}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_hotspot_ip_binding", cmd)
        return await self._transport().run(cmd)

    async def remove_hotspot_ip_binding(self, mac_address: str = "", address: str = ""):
        find_parts = []
        if mac_address:
            find_parts.append(f'mac-address={mac_address}')
        if address:
            find_parts.append(f'address={address}')
        if not find_parts:
            raise ValueError("mac_address or address required")
        cmd = f'/ip hotspot ip-binding remove [find {" ".join(find_parts)}]'
        log_event(self.device["id"], "remove_hotspot_ip_binding", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # PPP family: secrets, profiles, active sessions
    # ------------------------------------------------------------------

    TUNNEL_TYPES = ("l2tp", "pptp", "sstp", "ovpn", "pppoe")

    async def get_ppp_active(self):
        cmd = "/ppp active print detail without-paging"
        log_event(self.device["id"], "get_ppp_active", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def add_ppp_secret(self, name: str, password: str = "", service: str = "any",
                             profile: str = "default", local_address: str = "",
                             remote_address: str = "", comment: str = ""):
        cmd = f'/ppp secret add name={name} service={service} profile={profile}'
        if password:
            cmd += f' password={password}'
        if local_address:
            cmd += f' local-address={local_address}'
        if remote_address:
            cmd += f' remote-address={remote_address}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ppp_secret", cmd)
        return await self._transport().run(cmd)

    async def remove_ppp_secret(self, name: str):
        cmd = f'/ppp secret remove [find name={name}]'
        log_event(self.device["id"], "remove_ppp_secret", cmd)
        return await self._transport().run(cmd)

    async def set_ppp_secret(self, name: str, **kwargs):
        parts = [f'/ppp secret set [find name={name}]']
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f'{key}={value}')
        cmd = ' '.join(parts)
        log_event(self.device["id"], "set_ppp_secret", cmd)
        return await self._transport().run(cmd)

    async def kick_ppp_session(self, user: str):
        cmd = f'/ppp active remove [find name={user}]'
        log_event(self.device["id"], "kick_ppp_session", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # PPP family: servers (pptp/sstp/l2tp/ovpn) + pppoe instances
    # ------------------------------------------------------------------

    def _check_tunnel_type(self, tunnel_type: str):
        if tunnel_type not in self.TUNNEL_TYPES:
            raise ValueError(f"Invalid tunnel type '{tunnel_type}'. Allowed: {', '.join(self.TUNNEL_TYPES)}")
        return tunnel_type

    async def get_tunnel_server_status(self, tunnel_type: str):
        self._check_tunnel_type(tunnel_type)
        cmd = f"/interface {tunnel_type} server print"
        log_event(self.device["id"], "get_tunnel_server_status", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def set_tunnel_server(self, tunnel_type: str, enabled: bool = None, **kwargs):
        self._check_tunnel_type(tunnel_type)
        if enabled is not None:
            cmd = f'/interface {tunnel_type} server set enabled={"yes" if enabled else "no"}'
            log_event(self.device["id"], "set_tunnel_server", cmd)
            await self._transport().run(cmd)
        parts = []
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f'{key}={value}')
        if parts:
            cmd = f'/interface {tunnel_type} server set ' + ' '.join(parts)
            log_event(self.device["id"], "set_tunnel_server", cmd)
            return await self._transport().run(cmd)
        return ""

    async def get_pppoe_servers(self):
        cmd = "/interface pppoe server print detail without-paging"
        log_event(self.device["id"], "get_pppoe_servers", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def add_pppoe_server(self, service_name: str, interface: str,
                               default_profile: str = "default-encryption",
                               one_session_per_mac: str = "yes", comment: str = ""):
        cmd = (f'/interface pppoe server add service-name={service_name} interface={interface} '
               f'default-profile={default_profile} one-session-per-mac={one_session_per_mac}')
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_pppoe_server", cmd)
        return await self._transport().run(cmd)

    async def remove_pppoe_server(self, service_name: str):
        cmd = f'/interface pppoe server remove [find service-name={service_name}]'
        log_event(self.device["id"], "remove_pppoe_server", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # PPP family: clients (l2tp/pptp/sstp/ovpn/pppoe)
    # ------------------------------------------------------------------

    async def get_tunnel_clients(self, tunnel_type: str):
        self._check_tunnel_type(tunnel_type)
        cmd = f"/interface {tunnel_type}-client print detail without-paging"
        log_event(self.device["id"], "get_tunnel_clients", cmd)
        raw = await self._transport().run(cmd)
        return {"data": MikroTikParser.parse_records(raw), "raw": raw}

    async def add_tunnel_client(self, tunnel_type: str, name: str, target: str,
                                user: str, password: str = "", profile: str = "",
                                use_ipsec: bool = False, ipsec_secret: str = "",
                                add_default_route: bool = False, comment: str = ""):
        self._check_tunnel_type(tunnel_type)
        # pppoe-client uses "interface=" (physical iface), others use "connect-to="
        if tunnel_type == "pppoe":
            cmd = f'/interface pppoe-client add name={name} interface={target} user={user}'
        else:
            cmd = f'/interface {tunnel_type}-client add name={name} connect-to={target} user={user}'
        if password:
            cmd += f' password={password}'
        if profile:
            cmd += f' profile={profile}'
        if tunnel_type in ("l2tp", "pptp"):
            cmd += f' use-ipsec={"yes" if use_ipsec else "no"}'
            if ipsec_secret:
                cmd += f' ipsec-secret={ipsec_secret}'
        cmd += f' add-default-route={"yes" if add_default_route else "no"}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_tunnel_client", cmd)
        return await self._transport().run(cmd)

    async def remove_tunnel_client(self, tunnel_type: str, name: str):
        self._check_tunnel_type(tunnel_type)
        cmd = f'/interface {tunnel_type}-client remove [find name={name}]'
        log_event(self.device["id"], "remove_tunnel_client", cmd)
        return await self._transport().run(cmd)

    async def set_tunnel_client_state(self, tunnel_type: str, name: str, enabled: bool):
        self._check_tunnel_type(tunnel_type)
        action = "enable" if enabled else "disable"
        cmd = f'/interface {tunnel_type}-client {action} [find name={name}]'
        log_event(self.device["id"], "set_tunnel_client_state", cmd)
        return await self._transport().run(cmd)

    async def monitor_tunnel_client(self, tunnel_type: str, name: str):
        self._check_tunnel_type(tunnel_type)
        cmd = f'/interface {tunnel_type}-client monitor {name} once'
        log_event(self.device["id"], "monitor_tunnel_client", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # Parity with Cisco: health, save_config, ping, traceroute, OSPF config
    # ------------------------------------------------------------------

    async def health(self):
        """Reachability + system health check."""
        import asyncio
        result: dict = {"device_id": self.device["id"]}
        addr = self.device.get("management_address") or ""
        host = addr.split("/")[0]
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, 22), timeout=5.0
            )
            banner = await asyncio.wait_for(reader.readline(), timeout=3.0)
            writer.close()
            result["reachable"] = True
            result["ssh_banner"] = banner.decode(errors="replace").strip()
        except Exception as e:
            result.update(reachable=False, reason=f"TCP/22 unreachable: {e}")
            return result

        try:
            resource_out = await self._transport().run("/system resource print")
            # Parse resource output into structured JSON
            parsed_resource = MikroTikParser.parse_resource(resource_out)
            result["resource"] = {"data": parsed_resource, "raw": resource_out}
        except Exception as e:
            result["resource_error"] = str(e)

        return result

    async def save_config(self):
        """Save config and verify persistence."""
        out = await self._transport().run("/system backup save dont-encrypt=yes name=config-backup")
        # On MikroTik, /export is the source of truth; backup is binary.
        # Verify by reading back the backup name list.
        verify_out = await self._transport().run("/system backup print where name=config-backup")
        verified = "config-backup" in verify_out
        log_event(self.device["id"], "SAVE-VERIFY", f"backup verified={verified}")
        return {"saved": True, "verified": verified, "output": out}

    async def ping_tool(self, address: str, count: int = 3, interval: int = 1, size: int = 56):
        cmd = f"/ping address={address} count={count} interval={interval} size={size}"
        t0 = __import__("time").perf_counter()
        try:
            out = await self._transport().run(cmd)
        except Exception as e:
            log_event(self.device["id"], "PING", f"{address} x{count}", status="FAIL", error=str(e))
            raise
        duration = round((__import__("time").perf_counter() - t0) * 1000)
        # parse MikroTik ping output for packet loss
        import re
        m = re.search(r"(\d+) packets transmitted, (\d+) received", out)
        loss = 100
        if m:
            sent, recv = int(m.group(1)), int(m.group(2))
            loss = 100 - int(recv * 100 / sent) if sent else 100
        log_event(self.device["id"], "PING", f"{address} x{count}", status=f"OK loss={loss}%", duration_ms=duration)
        return {"data": out, "raw": out}

    async def traceroute_tool(self, address: str, max_hops: int = 30, packet_size: int = 56):
        cmd = f"/tool traceroute address={address} max-hops={max_hops} packet-size={packet_size}"
        out = await self._transport().run(cmd)
        return {"data": out, "raw": out}

    # ------------------------------------------------------------------
    # OSPF Configuration (ROS7 uses /routing/ospf/... structure)
    # ------------------------------------------------------------------

    async def add_ospf_instance(self, name: str, router_id: str = "", comment: str = ""):
        cmd = f'/routing ospf instance add name={name}'
        if router_id:
            cmd += f' router-id={router_id}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ospf_instance", cmd)
        return await self._transport().run(cmd)

    async def remove_ospf_instance(self, name: str):
        cmd = f'/routing ospf instance remove [find name={name}]'
        log_event(self.device["id"], "remove_ospf_instance", cmd)
        return await self._transport().run(cmd)

    async def add_ospf_area(self, instance: str, name: str, area_id: str = "", area_type: str = "default", comment: str = ""):
        cmd = f'/routing ospf area add instance={instance} name={name}'
        if area_id:
            cmd += f' area-id={area_id}'
        if area_type:
            cmd += f' type={area_type}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ospf_area", cmd)
        return await self._transport().run(cmd)

    async def add_ospf_interface_template(self, instance: str, area: str, interfaces: str, network_type: str = "broadcast", cost: int = 10, priority: int = 1, comment: str = ""):
        cmd = f'/routing ospf interface-template add instance={instance} area={area} interfaces={interfaces}'
        cmd += f' network-type={network_type} cost={cost} priority={priority}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ospf_interface_template", cmd)
        return await self._transport().run(cmd)

    async def add_ospf_network(self, instance: str, network: str, area: str, comment: str = ""):
        cmd = f'/routing ospf network add instance={instance} network={network} area={area}'
        if comment:
            cmd += f' comment="{comment}"'
        log_event(self.device["id"], "add_ospf_network", cmd)
        return await self._transport().run(cmd)

    async def remove_ospf_network(self, instance: str, network: str):
        cmd = f'/routing ospf network remove [find instance={instance} network={network}]'
        log_event(self.device["id"], "remove_ospf_network", cmd)
        return await self._transport().run(cmd)

    # ------------------------------------------------------------------
    # Config transaction parity (backup -> apply -> verify -> commit/rollback)
    # ------------------------------------------------------------------

    async def _txn_backup_export(self):
        out = await self._transport().run("/export file=txn-backup")
        return "txn-backup.rsc" in out

    async def _txn_rollback(self):
        try:
            out = await self._transport().run("/import file=txn-backup.rsc")
            ok = "completed" in out.lower() or "ok" in out.lower()
            return {"status": "OK" if ok else "?", "output": out[-300:].strip()}
        except Exception as e:
            return {"status": "FAIL", "output": str(e)}
        finally:
            try:
                await self._transport().run("/file remove txn-backup.rsc")
            except Exception:
                pass

    async def config_transaction(
        self,
        commands: list[str],
        verify: list[dict] | None = None,
        save_on_success: bool = False,
        description: str = "",
    ) -> dict:
        """Safe config transaction: export -> apply -> verify -> commit | rollback."""
        verify = verify or []
        report: dict = {"description": description, "steps": []}

        if not await self._txn_backup_export():
            report["status"] = "failed_preapply"
            report["reason"] = "export backup failed; no changes applied"
            return report

        # APPLY
        try:
            await self._logged("TXN-APPLY", "; ".join(commands), lambda: self.apply(commands))
            report["steps"].append({"phase": "apply", "status": "OK"})
        except Exception as e:
            rb = await self._txn_rollback()
            report.update(status="rolled_back", reason=f"apply failed: {e}", rollback=rb)
            return report

        # VERIFY
        failures = []
        for chk in verify:
            command = chk.get("command", "")
            expect = chk.get("expect")
            try:
                out = await self._transport().run(command)
                if expect and expect.lower() not in out.lower():
                    failures.append({"command": command, "reason": f"'{expect}' not found"})
            except Exception as e:
                failures.append({"command": command, "reason": str(e)[:200]})

        if failures:
            rb = await self._txn_rollback()
            report.update(status="rolled_back", verify_failures=failures, rollback=rb)
            return report

        report["steps"].append({"phase": "verify", "status": "OK", "checks": len(verify)})

        if save_on_success:
            await self.save_config()
            report["steps"].append({"phase": "save", "status": "OK"})

        try:
            await self._transport().run("/file remove txn-backup.rsc")
        except Exception:
            pass

        report["status"] = "committed"
        return report