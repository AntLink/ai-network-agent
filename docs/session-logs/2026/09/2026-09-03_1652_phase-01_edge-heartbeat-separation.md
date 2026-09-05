# Work Session: edge-heartbeat-separation

## Session Metadata

- Session ID: `20260903-165230-phase-01-edge-heartbeat-separation`
- Date/Time Started: `2026-09-03T16:52:30+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Extend the existing Edge control server and Central dispatch client so Edge presence liveness and TaskAttempt liveness have separate protocol paths and storage semantics.

## Scope

### In Scope
- Add session presence heartbeat and per-attempt task heartbeat endpoints to the existing control server.
- Ensure Edge task heartbeat reports liveness only; it does not renew the Central-owned lease.
- Add Central client methods and tests/documentation for both heartbeat types.

### Out of Scope
- Lease persistence, renewal policy, and recovery remain future TaskAttempt work.

## Initial Findings

- Existing Go control server had only a boolean ready-session map.
- Existing Central dispatch client had handshake and task dispatch but no heartbeat methods.
- mTLS remains enforced by `Serve`; handler tests use an in-memory HTTP test server.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Edge control session registry | `edge/internal/control/server.go` | `EXTEND` | Existing HELLO/READY/task gate | Preserve control channel and add typed liveness state. |
| Central Edge dispatch client | `backend/app/services/edge_dispatch.py` | `EXTEND` | Existing mTLS handshake/task dispatch | Add explicit presence/task heartbeat calls without a second client. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1649_phase-01_edge-handshake-readiness.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `M1-HB-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M1-HB-001 | Separate Edge presence and TaskAttempt heartbeat endpoints; Edge does not extend leases. | `edge/internal/control/server_test.go`; `go test ./...` | Go control tests and updated runbook | IMPLEMENTED_UNVERIFIED |

## Plan

1. Extend the existing `SessionRegistry` with session last-seen and per-attempt heartbeat timestamps.
2. Add `/v1/control/heartbeat` and `/v1/control/task-heartbeat` with ready-session checks.
3. Add Central client methods, tests, traceability, and runbook semantics.

## Work Log

### 2026-09-03T16:52:30+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1652_phase-01_edge-heartbeat-separation.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-01" --title "edge-heartbeat-separation" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T17:00:00+08:00 — Heartbeat separation implemented

**Action**
- Extended the existing Go control server registry from a boolean ready map to structured session records.
- Added separate session presence and TaskAttempt heartbeat endpoints.
- Added Central `EdgeDispatchClient.session_heartbeat()` and `.task_heartbeat()` methods.
- Explicitly kept lease authority in Central; Edge task heartbeat only records execution liveness.
- Updated traceability and deployment runbook.

**Files**
- `edge/internal/control/server.go`
- `edge/internal/control/server_test.go`
- `backend/app/services/edge_dispatch.py`
- `docs/traceability/requirements-matrix.md`
- `docs/runbooks/deployment-runbook.md`

**Commands executed**
```text
gofmt -w internal\control\server.go internal\control\server_test.go
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\go-build-cache-m1'); go test ./...
```

**Result**
- Go Edge packages passed.
- Control integration test now covers HELLO/READY, session heartbeat, task heartbeat, and typed task dispatch.

**Security / design decision**
- Heartbeat payloads contain session/attempt identifiers and timestamps only.
- No credentials or lease-extension authority is sent to or granted by the Edge heartbeat endpoints.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `docs/session-logs/2026/09/2026-09-03_1652_phase-01_edge-heartbeat-separation.md` | created | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | `go test ./...` from `edge/` | PASS |
| Lint | Not run yet | NOT RUN |
| Integration | `edge/internal/control/server_test.go` via Go test | PASS (in-memory HTTP handler; live mTLS pending) |
| Security/secret redaction | Code inspection of heartbeat payloads | PASS for this slice; broader redaction audit pending |

## Errors and Blockers

- No new errors. Live mTLS and GNS3 evidence remain unavailable in this session.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive endpoints; protocol version remains `1`.
- Rollback/recovery impact: revert the additive control/client changes; no durable data migration.

## Decisions / ADRs

- No ADR required; this extends the existing control channel with an explicit V5 heartbeat separation.

## Remaining Work

- Integrate heartbeat scheduling into the long-running Edge connection loop.
- Add durable Central TaskAttempt lease persistence and renewal authority.
- Prove live mTLS, enrollment, Cisco IOSv execution, audit, and UI result flow.

## Next Session Handoff

Start from:
- `edge/internal/control/server.go` now has separate heartbeat paths; Central lease persistence is still not complete.

Recommended next action:
1. Add a long-running Edge control client that periodically emits session heartbeat and emits task heartbeat while executing.
2. Then implement durable Central TaskAttempt lease authority and retry classification tests.

## Final Summary

Session is partially complete: heartbeat separation is implemented and unit-tested, while live mTLS/GNS3 and durable lease evidence remain pending.
