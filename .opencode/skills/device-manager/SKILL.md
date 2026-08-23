---
name: device-manager
description: Manage vendor-neutral inventory and capability model for network devices.
compatibility: OpenCode
---

# Device Manager (Inventory & Capabilities)

Manage device inventory and capabilities. Vendor-specific behavior belongs in vendor skill.

## Device Identity
Every device record supports:
- id, hostname, management_address, vendor, platform, os_version, model
- connection_profiles (ssh, api, rest, netconf)
- capabilities (ssh, api, vlans, routes, firewall, backup, rollback, etc.)
- status (active, maintenance, decommissioned)

## Capability Detection
1. Connect using configured transport.
2. Run minimal read‑only identification (via `device_identify` tool).
3. Parse vendor/platform/version.
4. Select the vendor skill.
5. Re‑run platform‑specific discovery.

## Multi-Device Operations
For fleet operations: discover targets, group by driver, collect read‑only, produce consolidated plan, require approval, limit concurrency (max 5).
