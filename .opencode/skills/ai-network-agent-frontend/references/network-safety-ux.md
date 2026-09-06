# Network Safety UX Rules

These rules apply whenever the frontend can trigger network changes.

## Risk classes

Use a simple risk classification:

- LOW — local, reversible, no management-plane impact expected
- MEDIUM — routing/VLAN/policy impact or multiple devices
- HIGH — management interface, authentication, AAA, routing core, VPN, firewall, destructive lab action
- CRITICAL — action may cause broad loss of access, erase configuration, or affect production-critical scope

Do not infer that a command is safe only because it is short.

## Destructive or lockout-prone examples

Treat operations involving these areas carefully:

- management IP/interface
- default route
- AAA/authentication
- SSH access
- privilege/enable settings
- firewall filters
- NAT
- routing protocol removal
- VLAN trunk changes
- `shutdown`
- configuration erase/reset
- lab destroy/delete
- restoring an old backup

## Required confirmation data

Before a risky execute action, show:

- device(s)
- management IP(s)
- action summary
- candidate configuration or diff
- risk level
- pre-check status
- backup status
- rollback availability
- expected verification

## Recommended controls

Use distinct actions such as:

- Plan Only
- Dry Run
- Approve & Execute
- Cancel
- Roll Back

Do not use misleading labels such as a generic `Save` button for an operation that actually pushes configuration to routers.

## Progress timeline

For configuration tasks, represent execution as explicit steps:

```text
Planning
Pre-check
Backup
Apply
Validate
Save/Commit
Complete
```

If rollback occurs:

```text
Failure detected
Rollback started
Rollback validated
Final state
```

## Failure behavior

A failed task must not disappear into a toast.

Provide:

- failing step
- timestamp
- backend error
- device scope
- partial-success state
- rollback status
- validation output

## Credentials

Credential forms may display masked secrets but must not fetch or reveal plaintext secrets unless the backend and security model explicitly require that capability.

Never persist secret values in browser storage.
