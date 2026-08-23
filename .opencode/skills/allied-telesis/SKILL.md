---
name: allied-telesis
description: Knowledge for managing Allied Telesis AlliedWare Plus.
compatibility: OpenCode
---

# Allied Telesis

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show system` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interface brief` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan` |

## Change Planning
- Cisco-like. `configure terminal`.
- Save: `write memory`.

## Rollback
- `configure replace` (newer models) or manual restore.
