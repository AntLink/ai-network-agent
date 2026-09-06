---
name: nine-router-lab-setup
description: Plan and configure 9-router Cisco/MikroTik/Aruba/GNS3 labs with compact, token-efficient workflows, batching, vendor-aware templates, safety checks, and concise validation output.
metadata:
  opencode/autoinvoke: "true"
---

# Nine Router Lab Setup

Use this skill when the user wants to configure, stabilize, validate, or document a 9-router lab while keeping token usage low.

The goal is not to print every full running-config. The goal is to work from a compact inventory, generate only needed changes, validate safely, and summarize results as tables/diffs.

## Token-efficient operating mode

Default to compact output unless the user asks for full configs.

Prefer:

- tables over paragraphs
- device groups over repeated per-device prose
- deltas over full configs
- command templates with variables over duplicated command blocks
- validation summaries over raw CLI dumps
- only failed device details, not all successful details

Avoid:

- pasting all 9 running-configs into the answer
- repeating identical commands 9 times when a template/table can describe them
- showing long raw command output unless troubleshooting requires it
- guessing topology or addressing when inventory can be read from project files/backend

## Required discovery

Before changing code or device configuration, gather only the minimum data needed:

1. Read project inventory or backend devices endpoint.
2. Identify the 9 routers by `device_id`, hostname, vendor, management IP, role, and lab.
3. Identify the requested feature: IP addressing, static routing, OSPF, BGP, NAT, VLAN/SVI, SSH, backups, monitoring, or validation.
4. Check existing backend integration docs if touching frontend/backend:
   - `docs/FRONTEND_BACKEND_INTEGRATION.md`
   - `.opencode/skills/ai-network-agent-backend-integration/SKILL.md`
5. Use vendor skills when vendor-specific behavior matters:
   - `cisco-ios`
   - `mikrotik-routeros`
   - `gns3-lab`

Do not ask the user to paste full configs if backend/device read endpoints can provide the needed facts.

## Compact inventory format

Represent the lab as one compact table:

| ID | Host | Vendor | Role | Mgmt IP | Links | Routing |
|----|------|--------|------|---------|-------|---------|
| r1 | R1 | cisco | edge | 172.22.x.x | r2,r3 | ospf |

If details are unknown, mark only that field as `unknown`; do not block the whole task unless the missing field is required for a destructive change.

## Batch planning pattern

For 9 routers, plan by groups:

- Same vendor + same feature = one template.
- Same role = one intent group.
- Device-specific values stay in a variable table.

Example:

```text
Template: Cisco OSPF area 0
Devices: R1,R2,R3,R4
Variables: router_id, networks
Risk: medium
Need approval: yes
```

Then output only:

- common template
- variable table
- generated diff summary
- validation commands

## Safe workflow

For any configuration change, use:

```text
Collect -> Plan -> Dry Run -> Approve -> Backup -> Deploy -> Verify -> Save
```

Never skip approval for changes that can affect:

- management IP
- default route
- routing protocol
- ACL/firewall
- NAT
- SSH/AAA/user/password
- interface shutdown/no shutdown
- lab node delete/rebuild/stop

The AI/LLM must not open SSH directly. Use backend tools, terminal session manager, or config workflow endpoints.

## Backend-first execution

Prefer project backend APIs:

- Read devices: `GET /api/v1/devices`
- Device facts: `GET /api/v1/devices/{device_id}/facts`
- Interfaces: `GET /api/v1/devices/{device_id}/interfaces`
- Routes: `GET /api/v1/devices/{device_id}/routes`
- Config read: `GET /api/v1/devices/{device_id}/config`
- Dry run: `POST /api/v1/config/plan`
- Apply: `POST /api/v1/config/apply`
- Rollback: `POST /api/v1/config/rollback`
- Terminal session: `/api/v1/terminal/sessions`

Use direct terminal commands mainly for validation, troubleshooting, or interactive lab checks. For production-style config changes, prefer config plan/apply.

## Vendor-aware compact templates

Cisco IOS interface IP:

```text
interface {{interface}}
 description {{description}}
 ip address {{ip}} {{mask}}
 no shutdown
```

MikroTik RouterOS interface IP:

```text
/ip address add address={{cidr}} interface={{interface}} comment={{description}}
/interface enable {{interface}}
```

Aruba AOS-CX interface IP:

```text
interface {{interface}}
 description {{description}}
 ip address {{cidr}}
 no shutdown
```

Cisco OSPF:

```text
router ospf {{process_id}}
 router-id {{router_id}}
 network {{network}} {{wildcard}} area {{area}}
```

MikroTik OSPF:

```text
/routing ospf instance add name={{name}} router-id={{router_id}}
/routing ospf area add name={{area_name}} instance={{name}} area-id={{area_id}}
/routing ospf interface-template add networks={{cidr}} area={{area_name}}
```

Use these as generation templates only. Validate against existing config and vendor/version before deployment.

## Output format for user

For normal progress updates, use this compact format:

```text
Scope: 9 routers, 3 vendor groups
Plan: OSPF area 0 + interface IP validation
Risk: medium
Need approval: yes
Blocked: none
Next: dry-run plan
```

For final result:

```text
Result: completed / partial / blocked
Changed: R1,R2,R3
Skipped: R4 no SSH, R5 missing interface
Verified: OSPF neighbors, routes, ping matrix
Failed: R5 Gi0/1 admin down
Docs/logs: updated
```

Only include raw CLI output for failed checks or when the user asks.

## Validation matrix

Use a compact validation table:

| Check | Devices | Pass | Fail | Notes |
|-------|---------|------|------|-------|
| SSH | 9 | 8 | 1 | R5 timeout |
| Interfaces up | 9 | 7 | 2 | R5 Gi0/1, R8 ether2 |
| Routing | 9 | 9 | 0 | OSPF full |
| Ping matrix | 9 | 8 | 1 | R5 isolated |

When a check fails, drill into only the failed device(s).

## Troubleshooting small issues

Use the narrow-fix pattern:

1. Reproduce exact command/endpoint/UI state.
2. Classify as frontend, backend, parser, device, inventory, or GNS3 issue.
3. Verify from the lowest reliable layer.
4. Patch only the owning layer.
5. Re-test the exact failed interaction.
6. Add a parser/service regression test when applicable.
7. Update docs/logs.

Examples:

- Cisco help incomplete: handle pagination and parser limits.
- MikroTik help wrong context: normalize `ip ?` to RouterOS `/ip` context in backend.
- Device detail unknown: normalize backend facts before rendering UI.
- Endpoint 404/502: verify route prefix and device/vendor mapping before changing UI.

## Stop conditions

Stop and ask before proceeding when:

- the 9-router inventory cannot be identified
- the requested change may lock out management access and no rollback path exists
- credentials are missing and cannot be read from backend environment/inventory
- GNS3 topology differs from intended cabling
- generated commands include destructive operations not explicitly approved

If blocked, return a compact blocker table with the exact missing data.
