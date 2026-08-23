---
name: whitebox-cumulus
description: Knowledge for managing Cumulus Linux whitebox switches.
compatibility: OpenCode
---

# Cumulus Linux

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `cat /etc/os-release`, `net show version` |
| `device_get_config` | `net show configuration` |
| `device_get_interfaces` | `net show interface`, `ip -json addr show` |
| `device_get_routes` | `net show route` |
| `device_get_vlans` | `net show vlan` |

## Change Planning (nclu)
- `net add bridge bridge ports swp1-10`
- `net add vlan 100 ip address 10.0.0.1/24`
- `net pending` (show diff)
- `net commit`

## Rollback
- `net rollback <id>`.
