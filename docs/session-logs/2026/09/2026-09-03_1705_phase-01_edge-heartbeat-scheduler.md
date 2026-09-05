# Work Session: edge-heartbeat-scheduler

## Session Metadata

- Session ID: `20260903-170508-phase-01-edge-heartbeat-scheduler`
- Date/Time Started: `2026-09-03T17:05:08+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add a reusable Edge heartbeat scheduler that emits presence and active TaskAttempt heartbeats independently.

## Scope

### In Scope
- Implement the scheduler behind a transport-neutral `HeartbeatSender` interface.
- Track and untrack active attempts safely.
- Prove cancellation, separation, and race safety with unit tests.

### Out of Scope
- Outbound Central transport integration and lease persistence remain future work.

## Initial Findings

- The previous session added heartbeat HTTP endpoints but did not provide a long-running scheduling component.
- The existing Edge control package is the correct extension point; no new service is needed.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Edge control package | `edge/internal/control/` | `EXTEND` | Existing handshake/task control server | Reuse package and isolate scheduling from transport. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1652_phase-01_edge-heartbeat-separation.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `M1-HB-001`, `TASK-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M1-HB-001 | Added independent presence/task heartbeat scheduler with no lease extension authority. | `go test -race ./internal/control` | `edge/internal/control/heartbeat_test.go` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Add `HeartbeatSender`, heartbeat DTOs, and `HeartbeatScheduler` to the existing control package.
2. Track active attempts and stop all loops on context cancellation.
3. Run normal and race-enabled Go tests; update traceability and handoff.

## Work Log

### 2026-09-03T17:05:08+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1705_phase-01_edge-heartbeat-scheduler.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-01" --title "edge-heartbeat-scheduler" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T17:12:00+08:00 — Scheduler implemented

**Action**
- Added transport-neutral `HeartbeatScheduler` with independent presence and task tickers.
- Added active-attempt tracking and cancellation behavior.
- Added recording-sender tests proving both heartbeat classes are emitted separately.

**Files**
- `edge/internal/control/heartbeat.go`
- `edge/internal/control/heartbeat_test.go`

**Commands executed**
```text
gofmt -w internal\control\heartbeat.go internal\control\heartbeat_test.go
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test -race ./internal/control
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test ./...
```

**Result**
- Control package passed race-enabled tests.
- All Edge packages passed.

**Security / design decision**
- Scheduler messages contain only session, Edge, boot, attempt, and timestamp metadata.
- Lease renewal remains outside the Edge scheduler and belongs to Central.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `edge/internal/control/heartbeat.go` | added | Transport-neutral heartbeat scheduling |
| `edge/internal/control/heartbeat_test.go` | added | Scheduler and race-safety evidence |
| `docs/session-logs/2026/09/2026-09-03_1705_phase-01_edge-heartbeat-scheduler.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | `go test ./...` from `edge/` | PASS |
| Lint | `gofmt` | PASS |
| Integration | Scheduler package tests | PASS; live Central transport pending |
| Security/secret redaction | DTO/code inspection | PASS for scheduler scope |

## Errors and Blockers

- No new errors. This is unit-level scheduling; it is not live mTLS evidence.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: none; uses existing heartbeat message semantics.
- Rollback/recovery impact: additive files only; no migration.

## Decisions / ADRs

- No ADR required; this is an extension of the existing control package.

## Remaining Work

- Connect `HeartbeatSender` to an authenticated outbound Central control transport.
- Register/unregister attempts around actual task execution.
- Implement durable Central lease renewal and recovery semantics.

## Next Session Handoff

Start from:
- `edge/internal/control/heartbeat.go` provides the scheduler; transport wiring is intentionally pending.

Recommended next action:
1. Implement outbound Edge mTLS/WebSocket control client using the scheduler interface.
2. Wire task execution lifecycle to `TrackAttempt`/`UntrackAttempt`.

## Final Summary

Session is partially complete: scheduler and tests are implemented; outbound transport and durable Central lease authority remain pending.
