---
name: nokia-sros
description: Knowledge for managing Nokia SR OS (7750 SR, 7450 ESS).
compatibility: OpenCode
---

# Nokia SR OS

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version` |
| `device_get_config` | `show configuration` |
| `device_get_interfaces` | `show router interface` |
| `device_get_routes` | `show router route-table` |
| `device_get_vlans` | `show service vlan` |

## Change Planning
- Enter: `configure candidate` or `configure exclusive`.
- Commands: `configure router interface "if-name" address 10.0.0.1/24`.
- Validate: `commit check`.
- Show diff: `commit compare`.
- Commit: `commit confirmed 5`.
- Save: `admin save-config`.

## Rollback
- `rollback to <id>`.
