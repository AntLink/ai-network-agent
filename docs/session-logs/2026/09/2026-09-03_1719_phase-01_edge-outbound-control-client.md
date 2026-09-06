# Work Session: edge-outbound-control-client

## Session Metadata

- Session ID: `20260903-171940-phase-01-edge-outbound-control-client`
- Date/Time Started: `2026-09-03T17:19:40+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add a typed outbound Edge control client using HTTPS/mTLS semantics and connect it to the existing heartbeat contract.

## Scope

### In Scope
- Implement HELLO/READY and presence/task heartbeat methods.
- Enforce HTTPS and bounded response handling.
- Add TLS test-server coverage.

### Out of Scope
- Real project PKI enrollment, WebSocket upgrade, reconnect backoff, and Central-side control endpoints remain future work.

## Initial Findings

- Existing `HeartbeatSender` is the intended transport seam.
- Existing security package already provides TLS 1.3 client configuration.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Edge control transport | `edge/internal/control/` | `EXTEND` | Existing heartbeat DTOs/scheduler and security TLS helpers | Add outbound client without duplicating heartbeat logic. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1705_phase-01_edge-heartbeat-scheduler.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `M1-HB-001`, `M1-PROTO-001`, `M1-EDGE-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M1-EDGE-001 | Outbound Edge client requires HTTPS and supports authenticated session establishment. | `go test -race ./internal/control` | `edge/internal/control/client_test.go` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Add outbound `Client` implementing `HeartbeatSender`.
2. Implement HELLO/READY and session-header heartbeat requests with bounded responses.
3. Verify with TLS test server and race-enabled tests.

## Work Log

### 2026-09-03T17:19:40+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1719_phase-01_edge-outbound-control-client.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-01" --title "edge-outbound-control-client" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T17:27:00+08:00 — Outbound client implemented

**Action**
- Added Edge-side HTTPS control client with HELLO/READY handshake.
- Implemented presence and TaskAttempt heartbeat sends through the existing `HeartbeatSender` contract.
- Enforced HTTPS, TLS config requirements for production construction, bounded response bodies, and sanitized status errors.
- Added TLS test-server coverage and HTTPS rejection coverage.

**Files**
- `edge/internal/control/client.go`
- `edge/internal/control/client_test.go`

**Commands executed**
```text
gofmt -w internal\control\client.go internal\control\client_test.go
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test -race ./internal/control
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test ./...
```

**Result**
- Control package passed race-enabled tests.
- All Edge packages passed.

**Security note**
- The production client rejects non-HTTPS URLs and requires a TLS config when it constructs its own HTTP transport.
- The test-only transport bypasses certificate verification solely for the ephemeral TLS test server; it is not used by production construction.

### 2026-09-03T17:45:00+08:00 — Lifecycle and reconnect wiring

**Action**
- Added `Client.Run()` with cancellation-aware reconnect and bounded exponential backoff.
- Connected scheduler error reporting to lifecycle reconnect handling.
- Added `--control-url` and `--boot-id` mode to the Edge binary while preserving listener and JSON-line modes.
- Added reconnect coverage verifying failed heartbeat causes a new HELLO session.

**Files**
- `edge/internal/control/client.go`
- `edge/internal/control/heartbeat.go`
- `edge/internal/control/client_test.go`
- `edge/cmd/ainet-edge/main.go`

**Commands executed**
```text
gofmt -w internal\control\heartbeat.go internal\control\client.go cmd\ainet-edge\main.go internal\control\client_test.go
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test -race ./...
```

**Result**
- All Edge packages passed race-enabled tests, including reconnect behavior.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `edge/internal/control/client.go` | added/extended | Outbound HTTPS control client and reconnect lifecycle |
| `edge/internal/control/heartbeat.go` | extended | Scheduler transport failure reporting |
| `edge/internal/control/client_test.go` | added/extended | TLS handshake, heartbeat, and reconnect evidence |
| `edge/cmd/ainet-edge/main.go` | extended | `--control-url` runtime mode |
| `docs/session-logs/2026/09/2026-09-03_1719_phase-01_edge-outbound-control-client.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | `go test ./...` from `edge/` | PASS |
| Lint | `gofmt` | PASS |
| Integration | TLS test server and reconnect test in `client_test.go` | PASS; live project PKI/Central pending |
| Security/secret redaction | Client payload/code inspection | PASS for control metadata; broader audit pending |

## Errors and Blockers

- No new errors. Live Central endpoint and project-issued certificates are not available.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: uses existing version 1 HELLO/READY and heartbeat paths.
- Rollback/recovery impact: additive files only; no migration.

## Decisions / ADRs

- No ADR required; extends the existing control transport seam.

## Remaining Work

- Add reconnect/backoff and long-running client lifecycle.
- Connect client to the scheduler in `main.go`.
- Implement Central control endpoint/WebSocket routing and durable leases.

## Next Session Handoff

Start from:
- `edge/internal/control/client.go` and `edge/cmd/ainet-edge/main.go` now provide a control-client runtime mode; live Central endpoints remain pending.

Recommended next action:
1. Add reconnecting Edge client lifecycle and scheduler wiring in `cmd/ainet-edge`.
2. Add Central endpoint support for the outbound control direction.

## Final Summary

Session is partially complete: outbound HTTPS client, scheduler lifecycle, reconnect, and binary wiring are implemented; live Central integration and WebSocket migration remain pending.
