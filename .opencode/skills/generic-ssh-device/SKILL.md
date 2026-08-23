---
name: generic-ssh-device
description: Fallback knowledge for unknown SSH devices. Read-only by default. Changes = CRITICAL + manual commands.
compatibility: OpenCode
---

# Generic SSH Device (Fallback)

Use ONLY when no vendor-specific skill matches.

## Rules
- **All operations default to READ-ONLY.**
- The agent NEVER generates change commands.
- Any change request is classified as **CRITICAL** risk.
- Operator MUST provide the exact command sequence.
- Operator MUST define the rollback plan before execution.

## Discovery (Minimal Probe)
- Connect via SSH.
- Send: `show version` (or `display version`, `help`).
- Parse first few lines to infer vendor.
- Do NOT send `show running-config` or other heavy commands without operator consent.

## Change Workflow
1. Operator provides exact, full command sequence.
2. Agent shows commands and asks for explicit approval.
3. Approval must be explicit: "execute these commands".
4. Tool executes them exactly as given.
5. Agent re‑runs read‑only discovery to verify.
6. Operator must confirm success or rollback manually.
