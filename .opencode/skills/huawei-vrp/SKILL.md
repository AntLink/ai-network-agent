---
name: huawei-vrp
description: Knowledge for managing Huawei VRP (S/AR/USG) devices.
compatibility: OpenCode
---

# Huawei VRP

Use standardized tools.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `display version` |
| `device_get_config` | `display current-configuration` |
| `device_get_interfaces` | `display interface brief` |
| `device_get_routes` | `display ip routing-table` |
| `device_get_vlans` | `display vlan` |

## Change Planning
- Enter `system-view`.
- Commands: `vlan 100`, `interface GigabitEthernet0/0/1`, `port link-type access`, `port default vlan 100`.
- Save: `save`.

## Rollback
- `rollback configuration` (if supported) or manual restore from backup.
