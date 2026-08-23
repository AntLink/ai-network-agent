---
name: zte-zxr10
description: Knowledge for managing ZTE ZXR10 switches/routers.
compatibility: OpenCode
---

# ZTE ZXR10

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interface brief` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan brief` |

## Change Planning
- Cisco-like. `configure terminal`.
- Save: `write` / `copy running-config startup-config`.

## Rollback
- `rollback` (check support).
