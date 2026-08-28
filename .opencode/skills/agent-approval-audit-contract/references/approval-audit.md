# Approval And Audit Contract

## Approval event

```ts
interface ApprovalEvent {
  type: "approval"
  id: string
  sessionId: string
  taskId: string
  title: string
  status: "required" | "approved" | "cancelled" | "expired"
  risk: "low" | "medium" | "high" | "critical"
  policy: "APPROVAL_REQUIRED"
  targets: Array<{
    type: "device" | "lab" | "workspace" | "inventory" | "topology"
    id: string
    name?: string
  }>
  commandsPreview?: string[]
  configPreview?: string
  diffPreview?: string
  backupRequired: boolean
  rollbackAvailable: boolean
  expiresAt?: string
}
```

## Approval required operations

```text
device config deploy
interface shutdown/no shutdown
IP/VLAN/routing changes
Linux service restart
package install
system file writes
workspace command that alters project state outside approved task
GNS3 project/node/link creation
GNS3 snapshot restore/delete
device inventory delete
credential profile changes
```

## Audit record

```ts
interface AuditRecord {
  id: string
  time: string
  user: string
  sessionId: string
  taskId: string
  approvalId?: string
  source: "User" | "AI Agent" | "Automation" | "API"
  action: string
  targetType: "device" | "lab" | "workspace" | "inventory" | "topology"
  targetId: string
  policy: "READ_ONLY" | "GUARDED" | "APPROVAL_REQUIRED" | "BLOCKED"
  risk: "low" | "medium" | "high" | "critical"
  result: "success" | "failed" | "cancelled" | "blocked"
  evidence: "backend_snapshot" | "live_command_output" | "generated_plan" | "dry_run" | "audit_record"
  summary: string
  error?: string
}
```

## Verification

Every execution should have post-checks:

```text
backup created when required
command returned success
device/session still reachable
expected config/state exists
unexpected errors absent
audit record stored
```

## UI rules

- Approval cards need `Approve`, `Cancel`, and `Modify Plan`.
- Show risk, targets, preview, backup status, and rollback availability.
- Do not hide command previews for config changes.
- Expired approvals must not execute.

