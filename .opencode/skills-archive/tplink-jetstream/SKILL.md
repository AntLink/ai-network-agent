---
name: tplink-jetstream
description: Knowledge for managing TP-Link JetStream switches.
compatibility: OpenCode
---

# TP-Link JetStream

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show system-info` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interfaces status` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan brief` |

## Change Planning
- Cisco-like. `configure terminal`.
- Commands: `vlan 100`, `name Sales`.
- Save: `copy running-config startup-config`.

## Rollback
- Manual restore from backup. `configure replace` on newer models.
