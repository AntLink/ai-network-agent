---
name: dlink-dgs
description: Knowledge for managing D-Link DGS switches.
compatibility: OpenCode
---

# D-Link DGS

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show switch` |
| `device_get_config` | `show running-config` |
| `device_get_vlans` | `show vlan` |
| `device_get_interfaces` | `show ports` |

## Change Planning
- `configure terminal` / `config`.
- VLAN: `config vlan 100 add untagged 1-5`.
- Save: `save config`.

## Rollback
- Manual restore from backup.
