---
name: extreme-networks
description: Knowledge for managing Extreme Networks (ExtremeXOS/VOSS).
compatibility: OpenCode
---

# Extreme Networks

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show switch` |
| `device_get_config` | `show configuration` |
| `device_get_interfaces` | `show ports` |
| `device_get_vlans` | `show vlan` |

## Change Planning (ExtremeXOS)
- `configure vlan Sales add port 1-10`.
- Save: `save configuration`.

## Rollback
- `restore configuration` from backup file.
