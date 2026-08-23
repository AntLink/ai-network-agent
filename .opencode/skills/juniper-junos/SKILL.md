---
name: juniper-junos
description: Knowledge for managing Juniper Junos devices via SSH/NETCONF.
compatibility: OpenCode
---

# Juniper Junos

Use standardized tools. Prefer NETCONF if available.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version` |
| `device_get_config` | `show configuration \| display set` |
| `device_get_interfaces` | `show interfaces terse` |
| `device_get_routes` | `show route` |
| `device_get_vlans` | `show vlans` |

## Change Planning
- Use candidate config: `configure exclusive`.
- Commands: `set` / `delete`.
- Validate: `commit check`.
- Show diff: `show | compare`.
- Commit: `commit confirmed 5` (auto‑rollback after 5 min).

## Rollback
- `rollback 0` (previous) or `rollback 1`.
- Tool `config_rollback` handles this.
