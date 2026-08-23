---
name: device-driver-authoring
description: Guidelines for creating new vendor drivers.
compatibility: OpenCode
---

# Device Driver Authoring

Use when adding a new vendor/platform.

## Driver Requirements
A driver must:
- implement the common `device_identify` logic.
- declare supported transports (SSH, API, NETCONF).
- declare capabilities.
- map vendor‑specific commands to standardized tool inputs (e.g., `device_get_facts`, `device_get_config`).

## Naming Convention
- Skill name format: `vendor-platform` (e.g., `arista-eos`, `huawei-vrp`).
- Place in `.opencode/skills/<name>/SKILL.md`.

## Checklist
1. Identify vendor/platform.
2. Define capabilities.
3. Add identification regex/pattern to `device_identify` tool.
4. Map commands:
   - `get_facts`: `show version` / `display version` / `system show`.
   - `get_config`: `show running-config` / `display current-configuration`.
   - `get_interfaces`: `show interfaces` / `display interface`.
   - `get_routes`: `show ip route` / `display ip routing-table`.
5. Define risk classifications for changes.
6. Add tests with mock outputs.
