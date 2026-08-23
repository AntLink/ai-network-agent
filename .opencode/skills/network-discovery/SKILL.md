---
name: network-discovery
description: Discover and inventory authorized network devices using safe probes.
compatibility: OpenCode
---

# Network Discovery

Discover devices that are already authorized in the inventory or provided by the operator. Do **not** perform aggressive port scanning.

## Discovery Workflow
1. Operator provides a list of IP addresses or hostnames (or references an inventory file).
2. Use `device_identify` tool on each target (SSH with minimal read‑only probe).
3. Parse vendor/platform/version.
4. Store results in Device Manager inventory.
5. Present discovered devices to operator for confirmation.

## Safe Probe Sequence
1. Connect via SSH (with timeout).
2. Send one of: `show version`, `display version`, `show system`, `cat /etc/os-release`, `help`.
3. Capture the first few lines to detect vendor.
4. Do **not** attempt exhaustive command enumeration.

## Constraints
- Only scan targets explicitly authorized by operator.
- Never scan beyond the provided list.
- Default to read-only.
