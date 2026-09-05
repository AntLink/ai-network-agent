# Work Session: mtls-control-channel-wiring

## Session Metadata

- Session ID: `20260903-164425-phase-01-mtls-control-channel-wiring`
- Date/Time Started: `2026-09-03T16:44:25+08:00`
- Date/Time Closed: `2026-09-03T16:58:00+08:00`
- Implementation Phase: `phase-01`
- Status: `PARTIAL`
- Operator: `Codex`
- Branch/commit: unavailable due git safe-directory ownership protection
- Starting worktree: dirty with extensive pre-existing changes

## Goal

Wire an authenticated Central mTLS dispatch client and Edge HTTPS control endpoint around the existing typed capability/protocol foundation.

## Scope

In scope: Central mTLS client configuration, Edge HTTPS/mTLS server, fixed read-only facts connector wiring, local credential resolution, and unit tests.  
Out of scope: certificate issuance/enrollment, ZeroTier, PostgreSQL/Redis/HA, and live Cisco IOSv execution.

## Reuse / Extend / Refactor / Create

| Component | Classification | Evidence / reason |
|---|---|---|
| Existing task API | `EXTEND` | `tasks.py` now dispatches through the centralized Edge client. |
| Existing settings | `EXTEND` | `core/config.py` adds explicit Edge mTLS settings with empty fail-closed defaults. |
| Edge protocol foundation | `EXTEND` | Existing envelope/journal retained; HTTP control validation added. |
| Edge runtime | `EXTEND` | Existing `edge/` CLI now supports configured mTLS control listener. |
| Device execution | `EXTEND` | Fixed `show version` connector and local keystore; no arbitrary command path. |

## Related Context

- Previous assessment: `docs/repository-assessment-v5.md`.
- Previous M1 session: `docs/session-logs/2026/09/2026-09-03_1638_phase-01_m1-edge-contract-foundation.md`.
- Requirements: `M1-PROTO-001`, `M1-CAP-001`, `M1-CRED-001`, `M1-DRV-001`.
- Traceability: `docs/traceability/requirements-matrix.md`.

## Work Log

### 2026-09-03T16:44:25+08:00 — Session opened

- Created this session log before the control-channel implementation.

### 2026-09-03T16:52:00+08:00 — Control wiring implemented

- Added `backend/app/services/edge_dispatch.py` using HTTPS-only `httpx` with CA verification and client certificate/key.
- Extended `tasks.py` to create a typed envelope and call the Edge client for Edge routes; missing configuration returns structured failure and never falls back to Central.
- Added Go `edge/internal/control` HTTPS handler with bounded body, Edge identity, capability, protocol, retry, validity, and credential-ref checks.
- Wired `ainet-edge` CLI control listener to mTLS config, local keystore, and fixed-command facts executor.
- Added Go control-channel tests and retained Python/Go contract tests.

Commands executed:

```text
python .agents\skills\ainet-zerotier-platform\scripts\new_session_log.py --phase phase-01 --title mtls-control-channel-wiring --operator Codex
$env:GOCACHE = (Join-Path (Get-Location) 'workspace\go-build-cache-m1'); gofmt -w ...; go test ./...
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\env\Scripts\python.exe -m pytest backend\tests\test_edge_contracts.py -q
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\env\Scripts\python.exe -m py_compile backend\app\schemas\edge.py backend\app\services\execution_routing.py backend\app\services\edge_dispatch.py backend\app\api\v1\endpoints\tasks.py
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend'); .\env\Scripts\python.exe -c "from app.main import app; print('/api/v1/tasks/capability' in app.openapi()['paths']); print('/api/v1/tasks/attempts/{attempt_id}' in app.openapi()['paths'])"
```

Results:

- Go tests: PASS for command, control, credentials, executor, and security packages.
- Python M1 tests: PASS — 3 passed.
- Python compilation: PASS.
- FastAPI route registration: PASS.
- Live Edge/Cisco/GNS3: NOT RUN.

## Files Changed

| File | Change |
|---|---|
| `backend/app/core/config.py` | extended with Edge mTLS settings |
| `backend/app/services/edge_dispatch.py` | created |
| `backend/app/schemas/edge.py` | extended with driver/idempotency fields |
| `backend/app/api/v1/endpoints/tasks.py` | wired Edge dispatch |
| `edge/cmd/ainet-edge/main.go` | wired control listener and facts executor |
| `edge/internal/control/server.go` | created |
| `edge/internal/control/server_test.go` | created |
| `edge/internal/security/mtls.go` | created in previous M1 session |
| `edge/internal/credentials/keystore.go` | created in previous M1 session |
| `edge/internal/executor/facts.go` | created in previous M1 session |
| `backend/tests/test_edge_contracts.py` | updated |
| `docs/session-logs/2026/09/2026-09-03_1644_phase-01_mtls-control-channel-wiring.md` | created/closed |

## Verification

| Check | Result |
|---|---|
| Go tests | PASS |
| Python M1 contract tests | PASS — 3 passed |
| Python compile/import/OpenAPI | PASS |
| Live mTLS with real certificates | NOT RUN — no project PKI material |
| Live Cisco IOSv facts | NOT RUN — no configured Edge/lab run |

## Errors and Blockers

- Real certificate issuance/enrollment and certificate-to-Edge tenant binding are not implemented.
- The Go facts connector uses system `ssh` with key/agent authentication only; no password fallback is allowed.
- Edge-local device inventory and central capability-result normalization are not wired to a live lab.
- Existing worktree remains dirty; unrelated changes were not reverted.

## Security / Licensing Notes

- Central requires `https://`, CA verification, and client certificate/key files; empty defaults fail closed.
- Edge requires mTLS server configuration, verifies client certificates, validates Edge ID and typed capability, and bounds request size.
- Credential values remain local to the keystore and are not included in task envelopes or logs.
- No ZeroTier or licensing decision was made.

## Compatibility / Recovery Notes

- Existing task API and routing remain canonical.
- If Edge dispatch fails, the attempt is marked failed; it is not retried or executed centrally automatically.
- No configuration-changing capability was added.

## Decisions / ADRs

- No ADR yet. Create one before declaring the mTLS transport/enrollment architecture durable.

## Remaining Work

- Implement one-time enrollment and project PKI lifecycle with ACTIVE/QUARANTINED/REVOKED/DELETED states.
- Add Edge boot/HELLO/WELCOME/READY handshake and session heartbeat separate from task heartbeat.
- Add durable attempt persistence/lease renewal and real Edge result normalization.
- Run fake-Edge integration, then live GNS3 Cisco IOSv evidence.

## Next Session Handoff

Start at `edge/internal/control/server.go`, `edge/cmd/ainet-edge/main.go`, `backend/app/services/edge_dispatch.py`, and `backend/app/api/v1/endpoints/tasks.py`. First add authenticated handshake/enrollment state and integration tests with generated test certificates; do not use production certificates or secrets in repository evidence.

## Final Summary

Central mTLS client and Edge control endpoint wiring are implemented and unit-tested. Enrollment, live device execution, and M1 acceptance evidence remain incomplete; status is PARTIAL and not production-ready.
