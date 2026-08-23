---
name: openwrt
description: Knowledge for managing OpenWrt routers/APs using UCI.
compatibility: OpenCode
---

# OpenWrt

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `ubus call system board`, `cat /etc/openwrt_release` |
| `device_get_config` | `uci show` |
| `device_get_interfaces` | `ip -json addr show`, `uci show network` |
| `device_get_routes` | `ip -json route show` |
| `device_get_vlans` | `uci show network` (DSA/switch) |

## Change Planning
- Use UCI: `uci set network.lan.ipaddr='10.0.0.1'`, `uci commit network`, `reload_config`.
- Wireless: `uci set wireless.@wifi-iface[0].ssid='MySSID'`, `wifi reload`.

## Rollback
- Backup `/etc/config/` via tar; restore if needed.
- `uci revert` for uncommitted changes.
