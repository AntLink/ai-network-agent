---
name: mikrotik-routeros
description: Knowledge for managing MikroTik RouterOS devices.
compatibility: OpenCode
---

# MikroTik RouterOS

Use standardized tools. Prefer REST API.

## Command Mappings (SSH fallback)
| Tool | Command |
|------|---------|
| `device_get_facts` | `/system resource print`, `/system identity print` |
| `device_get_config` | `/export compact` |
| `device_get_interfaces` | `/interface print` |
| `device_get_routes` | `/ip route print` |
| `device_get_vlans` | `/interface vlan print` |

## Change Planning
- Commands: `/ip address add address=10.0.0.1/24 interface=ether1`.
- Backup: `/export file=backup-{timestamp}`.
- Never change management IP without explicit HIGH risk approval.

## Rollback
- Restore from `/export` backup via `/import`.
