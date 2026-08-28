---
name: ciena-saos
description: Knowledge for managing Ciena SAOS packet/optical devices.
compatibility: OpenCode
---

# Ciena SAOS

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interfaces` |
| `device_get_routes` | `show ip route` |

## Change Planning
- `enable` -> `config`.
- Commands: `interface GigabitEthernet1/1`, `ip address 10.0.0.1/24`.
- Save: `save config`.

## Rollback
- `rollback` (check support).
