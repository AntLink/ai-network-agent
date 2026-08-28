---
name: aruba-aos-cx
description: Knowledge for managing Aruba AOS-CX switches and routers, including read-only inspection, VLAN/access/trunk interfaces, routing, config generation, verification, backup, and safety rules for AI Network Agent.
metadata:
  opencode/autoinvoke: "true"
---

# Aruba AOS-CX

Use this skill when the user or inventory target is Aruba AOS-CX:

```text
vendor=aruba
platform=aos-cx
```

This skill is vendor-specific. It complements:

- `agent-tool-registry-contract`
- `agent-intent-routing-policy`
- `configuration-safety`
- `network-runbook-skill`
- `ssh-network-device`

## Rules

- Do not mix Aruba AOS-CX syntax with Cisco IOS or MikroTik RouterOS.
- Prefer read-only inspection before suggesting changes.
- Configuration changes require plan, dry run, approval, backup, execute, verify, and audit.
- Use structured intent for changes. Backend Aruba driver should translate intent into AOS-CX commands.
- If the platform is older ArubaOS-Switch/ProCurve instead of AOS-CX, ask for clarification.

## References

Read the relevant reference before writing Aruba guidance:

- `references/commands.md`
- `references/config-patterns.md`
- `references/troubleshooting.md`
- `references/safety.md`

