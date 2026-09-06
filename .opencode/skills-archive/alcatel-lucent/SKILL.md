---
name: alcatel-lucent
description: Knowledge for managing Alcatel-Lucent OmniSwitch (AOS).
compatibility: OpenCode
---

# Alcatel-Lucent OmniSwitch

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show system` |
| `device_get_config` | `show configuration snapshot` |
| `device_get_interfaces` | `show interface status` |
| `device_get_vlans` | `show vlan` |

## Change Planning
- `configure terminal`.
- Commands: `vlan 100`, `name Sales`.
- Save: `write memory`.

## Rollback
- `rollback` (check version) or manual restore.
