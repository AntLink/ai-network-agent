---
name: ubiquiti-edgemax
description: Knowledge for managing Ubiquiti EdgeOS (Vyatta-based).
compatibility: OpenCode
---

# Ubiquiti EdgeMax (EdgeOS)

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version` |
| `device_get_config` | `show configuration` |
| `device_get_interfaces` | `show interfaces` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan` |

## Change Planning (Vyatta-style)
- `configure`
- `set interfaces ethernet eth0 address 10.0.0.1/24`
- `commit check`
- `compare` (show diff)
- `commit`
- `save`

## Rollback
- `rollback 1` or `rollback commit <id>`.
