---
name: arista-eos
description: Knowledge for managing Arista EOS switches.
compatibility: OpenCode
---

# Arista EOS

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version | json` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interfaces status` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan` |

## Change Planning
- Cisco-like. `configure terminal`.
- Commands: `vlan 100`, `name Sales`.
- Save: `write memory` / `copy running-config startup-config`.

## Rollback
- `configure replace flash:startup-config`.
