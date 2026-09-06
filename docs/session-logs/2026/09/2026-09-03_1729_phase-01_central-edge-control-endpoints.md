# Work Session: central-edge-control-endpoints

## Session Metadata

- Session ID: `20260903-172939-phase-01-central-edge-control-endpoints`
- Date/Time Started: `2026-09-03T17:29:39+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Add Central FastAPI control endpoints compatible with the outbound Edge HELLO/READY and heartbeat client.

## Scope

### In Scope
- Add typed, bounded request schemas and session state.
- Register endpoints in the existing V1 router.
- Test ready gating and separate heartbeats.

### Out of Scope
- Redis distributed session registry, mTLS termination/identity middleware, task dispatch, and durable lease state remain future work.

## Initial Findings

- Existing FastAPI V1 router is the canonical backend integration point.
- Edge client already defines the `/v1/control/*` message paths and response types.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| FastAPI V1 routing | `backend/app/api/v1/router.py` | `EXTEND` | Existing central API router | Add control router without parallel backend. |
| Edge session state | `backend/app/api/v1/endpoints/edge_control.py` | `CREATE` | No Central control endpoint existed | M1 ephemeral seam; Redis/HA later. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1719_phase-01_edge-outbound-control-client.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `M1-EDGE-001`, `M1-HB-001`, `HA-001`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M1-HB-001 | Central exposes ready-gated presence and TaskAttempt heartbeat paths; heartbeat does not renew lease. | `pytest backend/tests/test_edge_control.py -q` | `backend/tests/test_edge_control.py` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Create the typed Central control endpoint module.
2. Register it in the existing V1 router.
3. Test HELLO/READY and separate heartbeat behavior.

## Work Log

### 2026-09-03T17:29:39+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1729_phase-01_central-edge-control-endpoints.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-01" --title "central-edge-control-endpoints" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T18:05:00+08:00 — Central control endpoints implemented

**Action**
- Added typed Central HELLO, READY, presence heartbeat, and TaskAttempt heartbeat endpoints.
- Registered them in the existing FastAPI V1 router.
- Added ready-session gating and explicit non-lease heartbeat semantics.
- Added tests for successful handshake/heartbeats and rejection before READY.

**Files**
- `backend/app/api/v1/endpoints/edge_control.py`
- `backend/app/api/v1/router.py`
- `backend/tests/test_edge_control.py`
- `docs/traceability/requirements-matrix.md`
- `docs/runbooks/deployment-runbook.md`

**Commands executed**
```text
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m pytest backend\\tests\\test_edge_control.py backend\\tests\\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m py_compile backend\\app\\api\\v1\\endpoints\\edge_control.py backend\\app\\api\\v1\\router.py
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test ./...
```

**Result**
- Five focused Python tests passed.
- Python compilation passed.
- All Edge Go packages passed.

**Security / design decision**
- The endpoint module contains no credential or secret fields.
- Production deployment must put mTLS identity validation in front of these routes.
- In-process session state is explicitly M1-only and not HA-ready.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/api/v1/endpoints/edge_control.py` | added | Central Edge control contract |
| `backend/app/api/v1/router.py` | extended | Register control routes |
| `backend/tests/test_edge_control.py` | added | Handshake and heartbeat evidence |
| `docs/session-logs/2026/09/2026-09-03_1729_phase-01_central-edge-control-endpoints.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | Focused Python and Go commands above | PASS |
| Lint | Python compile | PASS |
| Integration | ASGI endpoint tests | PASS; live mTLS/Edge pending |
| Security/secret redaction | Schema and endpoint inspection | PASS for this scope; mTLS middleware pending |

## Errors and Blockers

- No new errors. Central endpoint state is intentionally in-memory and single-process for M1.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive `/api/v1/control/*` routes compatible with Edge client paths when BaseURL includes `/api`.
- Rollback/recovery impact: additive router/module/tests; no database migration.

## Decisions / ADRs

- No ADR required; existing FastAPI router is extended.

## Remaining Work

- Align Edge BaseURL deployment configuration with Central `/api/v1` prefix.
- Add mTLS identity middleware and replace in-memory state with Redis for HA.
- Add Central task dispatch/session routing and durable TaskAttempt lease authority.

## Next Session Handoff

Start from:
- `backend/app/api/v1/endpoints/edge_control.py` provides an M1-compatible control contract; it is not production HA or mTLS enforcement by itself.

Recommended next action:
1. Add Central mTLS identity enforcement and Edge registry persistence.
2. Add task dispatch through the Central session registry.

## Final Summary

Session is partially complete: Central control endpoints and focused tests are implemented; mTLS enforcement, Redis HA, and task dispatch remain pending.
