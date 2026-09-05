# Work Session: m1-edge-contract-foundation

## Session Metadata

- Session ID: `20260903-163803-phase-01-m1-edge-contract-foundation`
- Date/Time Started: `2026-09-03T16:38:03+08:00`
- Date/Time Closed: `2026-09-03T16:52:00+08:00`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch/commit: unavailable due git safe-directory ownership protection
- Starting worktree: dirty with extensive pre-existing changes

## Goal

Implement the first M1 capability/protocol foundation on top of the existing task and driver subsystems, without silently routing Edge work through Central.

## Scope

In scope: typed contracts, authoritative route resolver, canonical task capability endpoint, Go Edge protocol/journal skeleton, tests, traceability, and runbook.  
Out of scope: real mTLS enrollment, local SSH execution, ZeroTier, PostgreSQL/Redis, HA, and live GNS3 Edge acceptance.

## Initial Findings

- Existing task, device, Cisco driver, SSH transport, GNS3, safety, audit, and UI systems were reused/extended.
- No Edge runtime or control channel existed; `edge/` was created as the new runtime boundary.
- Previous assessment: `docs/repository-assessment-v5.md`.

## Reuse / Extend / Refactor / Create Assessment

| Component | Classification | Evidence / reason |
|---|---|---|
| Existing task API | `EXTEND` | `backend/app/api/v1/endpoints/tasks.py`; no parallel jobs domain. |
| Device/driver/transport | `REUSE_AS_IS` for this slice | `device_service.py`, `drivers/factory.py`, Cisco, SSH/console remain canonical. |
| Execution routing | `CREATE` | `backend/app/services/execution_routing.py`; no prior resolver existed. |
| Edge runtime/protocol | `CREATE` | `edge/`; no prior Edge/control implementation existed. |
| Credentials | `REFACTOR pending` | Contracts reject secret fields and use `credential_ref`; keystore remains pending. |

## Related Context

- Requirement IDs: `M1-EDGE-001`, `M1-PROTO-001`, `M1-ROUTE-001`, `M1-TASK-001`, `M1-CAP-001`, `M1-CRED-001`.
- Traceability: `docs/traceability/requirements-matrix.md`.
- Runbook: `docs/runbooks/deployment-runbook.md`.

## Work Log

### 2026-09-03T16:38:03+08:00 — Session opened

- Session log was created after initial implementation activity had begun; this ordering deviation is recorded transparently.

### 2026-09-03T16:42:00+08:00 — M1 foundation verified

- Added `backend/app/schemas/edge.py`, `backend/app/services/execution_routing.py`, and canonical task capability/attempt routes.
- Added `edge/go.mod`, Go protocol/executor skeleton, and Go tests.
- Added focused Python tests, traceability matrix, and deployment runbook.
- Added Go mTLS configuration, explicit local credential keystore, and fixed-command Cisco facts connector seams.

Commands executed:

```text
python .agents\skills\ainet-zerotier-platform\scripts\new_session_log.py --phase phase-01 --title m1-edge-contract-foundation --operator Codex
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\go-build-cache-m1'); go test ./...
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\env\Scripts\python.exe -m pytest backend\tests\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\env\Scripts\python.exe -c "from app.main import app; print('/api/v1/tasks/capability' in app.openapi()['paths']); print('/api/v1/tasks/attempts/{attempt_id}' in app.openapi()['paths'])"
```

Results: Go tests PASS; Python M1 tests PASS (3 passed); OpenAPI route check PASS. A prior full-suite run had baseline 42 passed, 5 failed, 2 errors due dirty inventory/console/temp-permission state.
The mTLS/keystore/executor Go tests also PASS.

## Files Changed

| File | Change |
|---|---|
| `backend/app/schemas/edge.py` | created |
| `backend/app/services/execution_routing.py` | created |
| `backend/app/api/v1/endpoints/tasks.py` | extended |
| `backend/tests/test_edge_contracts.py` | created |
| `edge/go.mod` | created |
| `edge/cmd/ainet-edge/main.go` | created |
| `edge/cmd/ainet-edge/main_test.go` | created |
| `edge/internal/security/mtls.go` | created |
| `edge/internal/security/mtls_test.go` | created |
| `edge/internal/credentials/keystore.go` | created |
| `edge/internal/credentials/keystore_test.go` | created |
| `edge/internal/executor/facts.go` | created |
| `edge/internal/executor/facts_test.go` | created |
| `docs/traceability/requirements-matrix.md` | created |
| `docs/runbooks/deployment-runbook.md` | created |
| `docs/session-logs/2026/09/2026-09-03_1638_phase-01_m1-edge-contract-foundation.md` | created/closed |

## Verification

| Check | Result |
|---|---|
| Go Edge tests | PASS |
| Python M1 contract tests | PASS — 3 passed |
| FastAPI route registration | PASS |
| Full existing backend suite | PARTIAL — baseline failures/errors documented |
| Live Edge/GNS3 | NOT RUN — not implemented |

## Errors and Blockers

- Session log creation occurred after code changes; recorded as a process deviation.
- Edge executor currently returns `NOT_CONFIGURED` for device I/O.
- mTLS/keystore/connector seams are present but not wired to enrollment, control server/client, or Edge inventory.
- Real mTLS enrollment/control channel and local keystore are not implemented.
- Worktree baseline is dirty; no unrelated changes were reverted.

## Security / Licensing Notes

- No secret values were added to code, logs, task payloads, or documentation.
- Envelope rejects secret-bearing payload fields and unsupported capabilities.
- mTLS requires CA, certificate, private key, client certificate verification, and TLS 1.3 minimum; no certificate material was created or logged.
- No ZeroTier/controller/license decision was made; upstream/license review remains pending.

## Compatibility / Recovery Notes

- Edge work fails closed with `EDGE_DISPATCH_NOT_CONFIGURED`; it does not fall back to Central.
- Existing task/driver/terminal/GNS3 behavior was preserved; new capability endpoint is additive.

## Decisions / ADRs

- No ADR yet; create one when mTLS/Edge execution transport becomes durable architecture.

## Remaining Work

- Wire mTLS enrollment and Central↔Edge transport.
- Connect the protected Edge-local keystore and fixed-command SSH facts connector to Edge inventory.
- Add fake-Edge integration, then Cisco IOSv GNS3 evidence and UI result wiring.

## Next Session Handoff

Start at `edge/internal/security/mtls.go`, `edge/internal/executor/facts.go`, `edge/cmd/ainet-edge/main.go`, `backend/app/schemas/edge.py`, and the M1 traceability matrix. Replace the explicit not-configured dispatcher boundary only after authenticated transport and credential handling are available.

## Final Summary

M1 protocol/routing/mTLS/keystore foundation is implemented and unit-tested. The real Central↔Edge secure dispatch and Cisco IOSv execution slice remains incomplete; status is PARTIAL and not production-ready.
