---
name: ruijie-rgos
description: Knowledge for managing Ruijie RGOS devices.
compatibility: OpenCode
---

# Ruijie RGOS

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interfaces brief` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan brief` |

## Change Planning
- Cisco-like. `configure terminal`.
- Commands: `vlan 100`, `name Sales`.
- Save: `write memory`.

## Rollback
- `configure replace` if supported.
