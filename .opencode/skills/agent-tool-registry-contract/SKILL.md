---
name: agent-tool-registry-contract
description: Define and maintain the AI Network Agent backend tool registry contract, including tool names, input/output schemas, policy classification, vendor scope, approval requirements, evidence type, and audit fields.
metadata:
  opencode/autoinvoke: "true"
---

# Agent Tool Registry Contract

Use this skill when designing or implementing backend tools for the AI Network Agent orchestrator.

The tool registry is the contract between:

- agent intent planning,
- backend execution,
- approval policy,
- audit logging,
- frontend event rendering.

Every tool must define:

```text
name
description
namespace
input_schema
output_schema
policy
vendor_scope
execution_scope
requires_approval
evidence_type
audit_fields
timeout_seconds
rollback_supported
```

Read `references/tool-registry.md` before implementing or changing tool routing.

