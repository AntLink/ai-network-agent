# Work Session: central-edge-identity-enforcement

## Session Metadata

- Session ID: `20260903-173216-phase-01-central-edge-identity-enforcement`
- Date/Time Started: `2026-09-03T17:32:16+08:00`
- Date/Time Closed: `OPEN`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch: `unknown`
- Starting Commit: `unknown`
- Starting Worktree: `unknown`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Require a trusted Edge certificate identity at Central control endpoints and propagate that identity from the outbound Edge client.

## Scope

### In Scope
- Add identity checks to HELLO, READY, presence heartbeat, and TaskAttempt heartbeat.
- Add the identity header to the Edge client.
- Test missing and mismatched identity rejection.

### Out of Scope
- Direct TLS termination in FastAPI, certificate issuance/enrollment, revocation, and trusted ingress deployment remain future work.

## Initial Findings

- Existing FastAPI control endpoint module and Go control client are extended.
- mTLS identity is represented by `X-Client-Edge-ID` only after a trusted proxy validates and strips/replaces it.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Central control endpoints | `backend/app/api/v1/endpoints/edge_control.py` | `EXTEND` | Existing HELLO/READY/heartbeat routes | Add fail-closed identity checks. |
| Edge control client | `edge/internal/control/client.go` | `EXTEND` | Existing HTTPS client | Propagate authenticated Edge identity metadata. |

Allowed classifications: `REUSE_AS_IS`, `EXTEND`, `REFACTOR`, `DEPRECATE`, `CREATE`, `UNKNOWN_NEEDS_INSPECTION`.

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_1729_phase-01_central-edge-control-endpoints.md`
- Relevant ADRs: <None or paths>
- Requirement IDs affected: `M1-EDGE-001`, `PKI-REVOCATION-002`
- Traceability matrix: `docs/traceability/requirements-matrix.md` (if initialized)

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M1-EDGE-001 | Control routes require trusted Edge identity and client propagates it. | `pytest backend/tests/test_edge_control.py -q`, `go test -race ./...` | `backend/tests/test_edge_control.py` | IMPLEMENTED_UNVERIFIED |

## Plan

1. Add fail-closed identity helper and apply it to Central control routes.
2. Add the identity header to Edge client requests.
3. Test missing identity and successful authenticated flow.

## Work Log

### 2026-09-03T17:32:16+08:00 — Session opened

**Action**
- Created mandatory engineering session log before code changes.

**Files**
- `docs/session-logs/2026/09/2026-09-03_1732_phase-01_central-edge-identity-enforcement.md`

**Commands executed**
```text
python .opencode/skills/ainet-zerotier-platform/scripts/new_session_log.py --phase "phase-01" --title "central-edge-identity-enforcement" --operator "Codex"
```

**Result**
- Session log created.

**Decision / rationale**
- Preserve implementation continuity, requirement traceability, and evidence for the next OpenCode/Codex session.

### 2026-09-03T18:00:00+08:00 — Edge identity enforcement implemented

**Action**
- Central control routes now require `X-Client-Edge-ID` and match it to the session/request Edge identity.
- Edge client now sends this identity header on control requests.
- Added tests for authenticated handshake/heartbeats and missing identity rejection.

**Files**
- `backend/app/api/v1/endpoints/edge_control.py`
- `backend/tests/test_edge_control.py`
- `edge/internal/control/client.go`
- `docs/traceability/requirements-matrix.md`
- `docs/runbooks/deployment-runbook.md`

**Commands executed**
```text
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m pytest backend\\tests\\test_edge_control.py backend\\tests\\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\\env\\Scripts\\python.exe -m py_compile backend\\app\\api\\v1\\endpoints\\edge_control.py
gofmt -w internal\\control\\client.go
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\\go-build-cache-m1'); go test -race ./...
```

**Result**
- Six focused Python tests passed.
- Python compilation passed.
- All Edge packages passed race-enabled tests.

**Security decision**
- The header is a trusted-ingress contract, not standalone authentication. Production ingress must terminate/verify mTLS, remove any client-supplied copy, and inject the verified Edge identity.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/api/v1/endpoints/edge_control.py` | extended | Fail-closed Edge identity checks |
| `backend/tests/test_edge_control.py` | extended | Identity enforcement evidence |
| `edge/internal/control/client.go` | extended | Propagate Edge identity header |
| `docs/session-logs/2026/09/2026-09-03_1732_phase-01_central-edge-identity-enforcement.md` | created/updated | Mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Unit tests | Focused Python and Go commands above | PASS |
| Lint | Python compile and `gofmt` | PASS |
| Integration | ASGI control endpoint tests | PASS; real mTLS ingress pending |
| Security/secret redaction | Header/schema inspection | PASS for identity scope; certificate/revocation evidence pending |

## Errors and Blockers

- No new errors. Header trust depends on deployment ingress controls.

## Security / Licensing Notes

- Do not place secrets, tokens, credentials, or private keys in this log.

## Compatibility / Recovery Notes

- Protocol/schema compatibility impact: additive HTTP identity header; no envelope change.
- Rollback/recovery impact: additive endpoint/client checks; no database migration.

## Decisions / ADRs

- No ADR yet; trusted-ingress identity contract may require an ADR before production deployment.

## Remaining Work

- Configure trusted mTLS ingress and certificate identity mapping.
- Implement durable Edge lifecycle/revocation state and force disconnect.
- Replace in-memory Central session registry with Redis HA.

## Next Session Handoff

Start from:
- Central routes now fail closed without identity header; production mTLS enforcement remains deployment-dependent.

Recommended next action:
1. Add trusted reverse-proxy configuration and integration evidence.
2. Add Redis-backed session registry and central task dispatch.

## Final Summary

Session is partially complete: identity checks and propagation are implemented/tested; trusted mTLS ingress, revocation, and HA state remain pending.
