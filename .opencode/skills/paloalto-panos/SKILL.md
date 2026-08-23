---
name: paloalto-panos
description: Knowledge for managing Palo Alto PAN-OS firewalls.
compatibility: OpenCode
---

# Palo Alto PAN-OS

Use standardized tools. Prefer REST API.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show system info` |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interface all` |
| `device_get_routes` | `show routing route` |

## Change Planning
- `configure`
- `set vsys vsys1 zone untrust network 1.2.3.4/24`
- `commit`

## Rollback
- `load config version <number>`.
