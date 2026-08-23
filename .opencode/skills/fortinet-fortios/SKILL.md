---
name: fortinet-fortios
description: Knowledge for managing FortiGate firewalls.
compatibility: OpenCode
---

# Fortinet FortiOS

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `get system status` |
| `device_get_config` | `show full-configuration` |
| `device_get_interfaces` | `show system interface` |
| `device_get_routes` | `get router info routing-table all` |

## Change Planning
- `config system interface`
- `edit port1`
- `set ip 10.0.0.1 255.255.255.0`
- `end`

## Rollback
- `execute rollback` (if supported) or restore from backup (`execute backup config`).
