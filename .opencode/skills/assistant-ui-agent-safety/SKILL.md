---
name: assistant-ui-agent-safety
description: Enforce approval, backup, and risk controls in assistant-ui workflows for the AI Network Agent dashboard so chat-driven network changes remain safe and auditable.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Agent Safety

Use this skill when the task affects risky network actions, approvals, or guardrails in the assistant UI.

## Core workflow

```text
Request -> Plan -> Validate -> Dry Run -> Approval -> Backup -> Execute -> Verify -> Audit
```

## Risk rules

- Read-only actions can stay lightweight.
- Write, delete, rollback, restore, destroy, and reload actions need explicit confirmation.
- High-risk changes must show impact, target devices, and backup state.
- The assistant UI should never make risky actions look like normal chat send.

## Required UI controls

- Approval card.
- Risk badge.
- Backup status.
- Cancel button.
- Dry run view.
- Post-change verification view.

## Backend boundary

- No SSH from browser.
- No credential storage in frontend.
- LLM produces intent and plan, not direct device access.

