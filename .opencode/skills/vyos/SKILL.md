---
name: vyos
description: Knowledge for managing VyOS routers.
compatibility: OpenCode
---

# VyOS

Identical to EdgeOS. Use `set`/`delete`/`commit`/`save`.

## Command Mappings
Same as Ubiquiti EdgeMax.

## Change Planning
- `configure`
- `set interfaces ethernet eth0 address 10.0.0.1/24`
- `commit check`
- `compare`
- `commit`
- `save`

## Rollback
- `rollback <id>`.
