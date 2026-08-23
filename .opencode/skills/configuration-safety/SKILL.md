---
name: configuration-safety
description: Mandatory safety rules for planning, approval, backup, application, verification, and rollback.
compatibility: OpenCode
---

# Configuration Safety (Policy Layer)

This skill is referenced by `policy_check` tool. Do not bypass.

## Risk Definitions
| Level | Examples | Policy |
|-------|----------|--------|
| LOW | Adding a VLAN (non-management), creating a user, viewing logs | Auto-approve possible if operator grants flag |
| MEDIUM | Changing DHCP pool, non-management firewall rule, static route | Explicit approval required |
| HIGH | Changing management IP, default route, SSH/AAA, WAN interface | Mandatory impact warning + explicit approval |
| CRITICAL | Factory reset, mass changes (>10 devices), destructive ops | Must be broken down; never fully automated |

## Mandatory Workflow for Changes
1. Collect current state.
2. Create backup (`config_backup`).
3. Generate plan (`config_plan`).
4. Validate (`config_validate`).
5. Show diff.
6. Check policy (`policy_check`).
7. Request approval.
8. Apply (`config_apply`).
9. Verify (`config_verify`).
10. If verification fails, rollback (`config_rollback`).

## Audit
Every change must generate an immutable audit event (logged by `network-auditor`).

## Persistence Verification (mandatory, learned 2026-08-23)

A save can LIE. On GNS3 vIOS nodes with broken flash (wrong disk
interface), `write memory` prints `[OK]` while nothing is written;
the config then vanishes on the next reload.

After ANY `write memory` / `copy run start`, verify with a pattern that
covers ALL key stanzas of the change, e.g.:

```
show startup-config | include hostname|router ospf|access vlan|mode trunk|ip address
```

Checking only the hostname is insufficient — partial saves pass that test.
If the startup-config lacks any expected stanza: re-apply, re-save,
re-verify before declaring success. See `gns3-lab` skill for the root
cause (IDE vs SATA disk interface).
