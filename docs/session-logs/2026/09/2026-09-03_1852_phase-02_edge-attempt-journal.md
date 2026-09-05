# Work Session: edge-attempt-journal

## Session Metadata

- Session ID: `20260903-185224-phase-02-edge-attempt-journal`
- Date/Time Started: `2026-09-03T18:52:24+08:00`
- Date/Time Closed: `2026-09-03T19:04:00+08:00`
- Implementation Phase: `phase-02`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add Edge-side duplicate-delivery protection for the same TaskAttempt/idempotency key using a bounded runtime journal.

## Scope

### In Scope
- Record successful terminal results and return them for duplicate delivery.
- Reject concurrent duplicate delivery while the original attempt is executing.
- Add Go race-tested evidence and operational documentation.

### Out of Scope
- Durable disk-backed journal, reconnect reconciliation, and production Edge keystore integration.

## Initial Findings

 - Existing Go control server and SessionRegistry are canonical.
 - Capability remains fixed to `device.read.facts`; no arbitrary shell path is added.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Edge control server | `edge/internal/control/server.go` | `EXTEND` | Existing mTLS/control handler owns task acceptance | Add bounded journal at the accepted-attempt boundary |
| Go control tests | `edge/internal/control/server_test.go` | `EXTEND` | Existing handshake/task test covers the canonical path | Prove duplicate result reuse |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1847_phase-02_atomic-dispatch-claim.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `M1-PROTO-001`, `TASK-LEASE-001`, `EDGE-JOURNAL-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| EDGE-JOURNAL-001 | Bounded Edge journal, terminal duplicate result, in-flight duplicate rejection | `go test -race ./...` | `docs/traceability/requirements-matrix.md` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Inspect the Go control acceptance path and existing tests.
2. Add bounded duplicate journal and in-flight fence.
3. Run normal and race tests.
4. Update durable handoff documentation.

## Work Log

### 2026-09-03T18:58:00+08:00 — Edge journal implemented

**Action**
- Added bounded `attempt_id` + idempotency journal to the existing Go `SessionRegistry`.
- Returned terminal results for duplicate delivery and rejected in-flight duplicates with `409`.
- Added a test proving the handler executes once for repeated delivery.

**Decision / rationale**
- `EXTEND` the existing control server; do not create a parallel queue or executor.
- Keep the journal metadata/result-only and bounded. Durable journal/reconnect reconciliation remains a later production task.

### 2026-09-03T18:52:24+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1852_phase-02_edge-attempt-journal.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-02" --title "edge-attempt-journal" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `edge/internal/control/server.go` | extended | Bounded terminal/in-flight attempt journal |
| `edge/internal/control/server_test.go` | extended | Duplicate delivery proof |
| `docs/traceability/requirements-matrix.md` | updated | `EDGE-JOURNAL-001` |
| `docs/runbooks/deployment-runbook.md` | updated | Journal operational semantics |
| `docs/session-logs/index.md` | updated | Session index |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Go unit tests | `go test ./...` from `edge/` | PASS: all packages |
| Go race tests | `go test -race ./...` from `edge/` | PASS: all packages |
| Integration | Live Central/Edge/GNS3 not run | NOT RUN: runtime evidence pending |
| Security/secret redaction | Journal contains task result metadata only; no credential fields added | PASS for this slice |

## Errors and Blockers

- The journal is process-local; an Edge restart loses the in-memory result journal. Durable bounded storage and reconnect reconciliation are required before production.
- The first Go test command was run from repository root and failed because no Go module exists there; rerun from `edge/` passed.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: duplicate responses add `duplicate_delivery=true` only on repeated terminal delivery; task envelope schema is unchanged.
- Rollback/recovery impact: duplicate execution is fenced during process lifetime; restart recovery remains pending.

## Decisions / ADRs

- None; this is a bounded extension of the existing Edge control registry.

## Remaining Work

- Replace process-local journal with durable bounded Edge storage.
- Add in-flight duplicate test with concurrent requests and reconnect journal reconciliation.
- Prove Central -> Edge -> Cisco IOSv behavior in GNS3.

## Next Session Handoff

Start from:
- `edge/internal/control/server.go` journal implementation.
- `edge/internal/control/server_test.go` duplicate test.

Recommended next action:
1. Add durable journal persistence and unresolved-attempt reconciliation during Edge reconnect.

## Final Summary

Edge now prevents duplicate execution for repeated delivery during its process lifetime. Race-tested Go verification passes; durable restart recovery and live GNS3 evidence remain pending, so this session is PARTIAL.
