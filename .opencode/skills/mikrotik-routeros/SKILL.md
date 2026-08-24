---
name: mikrotik-routeros
description: Knowledge for managing MikroTik RouterOS devices.
compatibility: OpenCode
---

# MikroTik RouterOS

Use standardized tools. Prefer REST API.

## Command Mappings (SSH fallback)
| Tool | Command |
|------|---------|
| `device_get_facts` | `/system resource print`, `/system identity print` |
| `device_get_config` | `/export compact` |
| `device_get_interfaces` | `/interface print` |
| `device_get_routes` | `/ip route print` |
| `device_get_vlans` | `/interface vlan print` |

## Change Planning
- Commands: `/ip address add address=10.0.0.1/24 interface=ether1`.
- Backup: `/export file=backup-{timestamp}`.
- Never change management IP without explicit HIGH risk approval.

## Rollback
- Restore from `/export` backup via `/import`.

## Version Differences (ROS6 vs ROS7)

**OSPF** — ROS7 uses `/routing/ospf/instance`, `/routing/ospf/area`, `/routing/ospf/interface-template`, `/routing/ospf/network`. ROS6 used `/routing ospf instance` etc. Driver abstracts this; prefer ROS7 syntax.

**OSPF Configuration (ROS7)** — Use these driver methods / API endpoints:
- `add_ospf_instance(name, router_id?, comment?)`
- `add_ospf_area(instance, name, area_id?, area_type?, comment?)`
- `add_ospf_interface_template(instance, area, interfaces, network_type?, cost?, priority?, comment?)`
- `add_ospf_network(instance, network, area, comment?)`

**Wireless** — ROS7 moved `/interface wireless` → `/interface wifi` (driver handles both).

## Parity with Cisco Driver (Phase F2)

| Feature | Cisco | MikroTik |
|---------|-------|----------|
| Health check | ✅ `health()` | ✅ `health()` |
| Save with verification | ✅ `save_config()` | ✅ `save_config()` (backup + verify) |
| Ping / Traceroute | ✅ `ping_tool()` / `traceroute_tool()` | ✅ `ping_tool()` / `traceroute_tool()` |
| Config Transaction (backup→apply→verify→commit/rollback) | ✅ `config_transaction()` | ✅ `config_transaction()` |
| OSPF config | ✅ `set_ospf_*` | ✅ `add_ospf_instance/area/interface-template/network` |
| Save verification | ✅ startup-config compare | ✅ backup file verify |

## API Response Format (2026-08-24)

**All MikroTik driver methods now return structured JSON:**

```python
# READ methods (GET) -> {"data": <structured>, "raw": "<original_cli_text>"}
{
    "data": <parsed_structured_data>,
    "raw": "<original_cli_text>"
}

# WRITE methods (POST/DELETE/PATCH) -> normalized via write_response helper
{
    "status": "applied",           # applied | deleted | saved | committed | failed
    "operation": "add_vlan",       # driver method name
    "success": true,
    "output": ""                   # raw device output (usually empty / warning)
}
```

**Available Parsers in `backend/app/drivers/mikrotik/parser.py` (MikroTikParser):**
- `parse_records()` - GENERIC parser for `print detail` output (key=value
  multi-line records, quoted values, flag-led records tanpa index seperti
  routes `DAd`). Dipakai oleh ~25 read methods.
- `parse_resource()` / `parse_identity()` - colon `key: value` format
  (resource, identity, snmp, ntp, dns)
- `parse_config()` - /export terse

**RouterOS output dua bentuk:**
- `print detail` (tables) → `key=value` multi-line records → `parse_records()`
- `print` (single object: /snmp, /ip dns, /system ntp client) → `key: value`
  colon → `parse_resource()`

**Note:** All read methods in the driver use these parsers to return structured data.
Raw CLI text is always included in the `raw` field for debugging and backward compatibility.

## API Endpoints (MikroTik)

All under `/api/v1/mikrotik/{device_id}/...`

### Read-only
- `GET /resources/ip-addresses`
- `GET /resources/pools`
- `GET /resources/dhcp-servers`
- `GET /resources/dhcp-leases`
- `GET /resources/bridges`
- `GET /resources/bridge-ports`
- `GET /resources/firewall/filter|nat|mangle|address-lists`
- `GET /resources/ospf` `/bgp` `/static-routes`
- `GET /resources/ppp-secrets` `/ppp-profiles`
- `GET /resources/wireless` `/wireless-security-profiles`
- `GET /resources/snmp` `/users` `/logging` (config rules: topics/action)
- `GET /resources/log/messages` (riwayat log `/log print`: time/topics/message)
- `GET /resources/hotspot/servers|profiles|users|user-profiles|active|hosts|ip-bindings|walled-garden`
- `GET /resources/ppp-active`
- `GET /resources/tunnel/{type}/server`
- `GET /resources/pppoe-servers`
- `GET /resources/tunnel/{type}/clients`

### Write (Config)
- `POST /ip-address` — add IP
- `DELETE /ip-address` — remove IP
- `POST /vlan` / `DELETE /vlan` — VLAN mgmt
- `POST /bridge` — add bridge
- `POST /bridge/port` / `DELETE /bridge/port` — bridge ports
- `POST /static-route` / `DELETE /static-route`
- `POST /firewall/filter` / `DELETE /firewall/filter/{num}`
- `POST /firewall/nat` / `DELETE /firewall/nat/{num}`
- `POST /firewall/address-list` / `DELETE /firewall/address-list`
- `POST /ip-pool` / `DELETE /ip-pool`
- `POST /dhcp-server`
- `POST /interface/set` / `POST /interface/{name}/enable|disable`
- `POST /system/identity`
- `POST /system/users` / `DELETE /system/users/{name}`
- `POST /system/ntp`
- `POST /system/dns`
- `POST /wireless/security-profile`

### Hotspot
- `GET /resources/hotspot/servers|profiles|users|user-profiles|active|hosts|ip-bindings|walled-garden`
- `POST /hotspot/server` / `DELETE /hotspot/server` / `POST /hotspot/server/{name}/enable|disable`
- `POST /hotspot/user` / `DELETE /hotspot/user` / `PATCH /hotspot/user` / `POST /hotspot/user/{name}/reset-counters`
- `POST /hotspot/reset-counters-all`
- `POST /hotspot/kick`
- `POST /hotspot/user-profile` / `DELETE /hotspot/user-profile`
- `POST /hotspot/ip-binding` / `DELETE /hotspot/ip-binding`

### PPP / VPN
- `GET /resources/ppp-active`
- `POST /ppp/secret` / `DELETE /ppp/secret` / `PATCH /ppp/secret`
- `POST /ppp/kick`
- `GET /resources/tunnel/{type}/server`
- `PATCH /tunnel/{type}/server`
- `GET /resources/pppoe-servers`
- `POST /pppoe/server-instance` / `DELETE /pppoe/server-instance`
- `GET /resources/tunnel/{type}/clients`
- `POST /tunnel/client` / `DELETE /tunnel/client`
- `POST /tunnel/{type}/client/{name}/{enable|disable|monitor}`

### New (Parity)
- `GET /health` — reachability + resource info
- `POST /tools/ping` — ping with count/interval/size
- `POST /tools/traceroute` — traceroute
- `POST /config/save` — save with verification
- `POST /config/transaction` — backup→apply→verify→commit/rollback
- `POST /ospf/instance` / `DELETE /ospf/instance`
- `POST /ospf/area`
- `POST /ospf/interface-template`
- `POST /ospf/network` / `DELETE /ospf/network`

### Utility
- `POST /commands/run` — raw commands
- `POST /monitoring` — cpu/memory/disk/temperature/voltage

## ROS7 Syntax Notes
- OSPF moved to `/routing/ospf/...`
- Wireless: `/interface wifi` (driver handles both)
- Bridge VLAN filtering: `/interface bridge vlan`
- Use `find` with brackets for removes: `remove [find name=x]`