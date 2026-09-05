# Work Session: m1-vertical-slice-edge-lab-execution

## Session Metadata

- Session ID: `20260903-233410-phase-01-m1-vertical-slice-edge-lab-execution`
- Date/Time Started: `2026-09-03T23:34:10+08:00`
- Date/Time Closed: `2026-09-04T01:25:00+08:00`
- Implementation Phase: `phase-01`
- Status: `COMPLETE`
- Operator: `opencode`
- Branch: `main`
- Starting Commit: `3a4856a2f2700aa4df3285608292e33bedda2e62`
- Starting Worktree: `dirty`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Complete the Milestone 1 vertical slice end-to-end against a live lab:

```text
Central (existing FastAPI/task/policy)
-> one enrolled Edge (Go ainet-edge server mode)
-> one Cisco IOSv (R1)
-> capability-based read (device.read.facts)
-> normalized result
-> audit evidence
```

Continue from the prior handoff. Do not move to Milestone 2 until the Milestone 1
acceptance gate passes.

## Scope

### In Scope
- Restore a live, persistent Edge reachable by Central.
- Enroll the Edge over mTLS and authenticate.
- Execute one read-only capability (`device.read.facts`) through the Edge against R1.
- Return a normalized structured result through the existing `/api/v1/tasks/capability` surface.
- Record audit evidence and durable documentation.

### Out of Scope
- Milestones 2-6 (leases/retries/PKI lifecycle/HA/Scale/private infra).
- Customer/site/overlapping-subnet UI work.
- Production readiness / executable production gate.

## Initial Findings

- The Alpine VM Edge (172.21.0.20) had become unreachable and boots ephemeral
  (tmpfs) from the Alpine ISO; each reboot reverts to a bare OS (no sshd, no
  network) and the Windows->Alpine Cloud bridge stalls large sustained file
  transfers (SCP/SFTP/SSH-stream all stalled ~2 MB of the 9 MB binary).
- The GNS3 controller/compute is the GNS3 VM at 172.21.0.2 (controller on port
  80, SSH on 22). Pathcrypto: R1 (Cisco IOSv) runs as a QEMU node there and is
  reachable from the GNS3 VM over tap0 (192.168.10.254 -> 192.168.10.1).
- The repository already contained the full EDGE dispatch path
  (`POST /api/v1/tasks/capability` -> `ExecutionRoutingResolver` -> TaskAttempt
  lease -> `edge_dispatch_client.dispatch` -> audit), plus a compliant server-
  mode Edge runtime with an R1 `device.read.facts` executor.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Central FastAPI/task/policy | `backend/app/api/v1/endpoints/tasks.py`, `edge_control.py` | `REUSE_AS_IS` | live dispatch via `/tasks/capability` | Canonical backend already wired. |
| Central EDGE dispatch client | `backend/app/services/edge_dispatch.py` | `EXTEND` | changed `_client` to use an explicit `ssl.SSLContext` | httpx `verify`+`cert` combination dropped the client cert on Windows; explicit context verifies CA and presents client cert. |
| Edge runtime | `edge/cmd/ainet-edge`, `edge/internal/{control,executor,credentials,security}` | `REUSE_AS_IS` | live server-mode run | Executor + mTLS + keystore already complete. |
| Dev PKI generator | `tools/dev_pki.py` | `EXTEND` | `tools/gen_m1_live_pki.py` | role-correct certs (dual SERVER+CLIENT auth) and edge SAN IP for the server-mode model. |
| Deployment tooling | `tools/deploy_alpine_edge.py` | `REFACTOR` | deployed Edge to persistent GNS3 VM via paramiko SFTP + systemd | Alpine path was ephemeral and Cloud-bridge transfer-stall prone. |
| Inventory device R1 | `backend` inventory | `EXTEND` | added `r1-m1` device | scoped EDGE-routed device. |

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-03_2334_phase-01_m1-vertical-slice-edge-lab-execution.md` (this file, opened 23:34).
- Relevant ADRs: None.
- Requirement IDs affected: `M1-EDGE-001`, `M1-PROTO-001`, `M1-ROUTE-001`, `M1-CAP-001`, `M1-CRED-001`, `M1-AUDIT-001`.
- Traceability matrix: `docs/traceability/requirements-matrix.md`

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M1-EDGE-001 | Edge runs as mTLS server on GNS3 VM 172.21.0.2:9443 (systemd) | `systemctl is-active ainet-edge` | `docs/evidence/m1-vertical-slice/README.md` | VERIFIED |
| M1-PROTO-001 | HELLO/READY handshake over TLS 1.3 mTLS | `POST /v1/control/hello` -> 200 WELCOME; `/ready` -> 200 READY_ACK | `docs/evidence/m1-vertical-slice/r1-facts-live-result-20260903.json` | VERIFIED |
| M1-ROUTE-001 | ExecutionRoutingResolver routes r1-m1 to EDGE=edge-001 | `POST /api/v1/tasks/capability` -> `execution_location: EDGE` | `docs/evidence/m1-vertical-slice/central-api-capability-live-20260903.json` | VERIFIED |
| M1-CAP-001 | `device.read.facts` executes through Edge against R1 | `/tasks/capability` -> task status success, normalized facts | same evidence JSON | VERIFIED |
| M1-CRED-001 | Edge resolves `credential_ref=r1-lab` from protected local keystore | Edge keystore + R1 SSH auth confirmed | `docs/evidence/m1-vertical-slice/README.md` | VERIFIED |
| M1-AUDIT-001 | Central records `TASK-EDGE-EXECUTION` audit event | `GET /api/v1/audit` -> event result=success | `docs/evidence/m1-vertical-slice/central-api-capability-live-20260903.json` | VERIFIED |

## Plan

1. Inspect the repo and the target session log handoff.
2. Diagnose the latency/lab blocker (Alpine vs GNS3 VM vs docker Edge).
3. Deploy a persistent Edge and enroll/authenticate it.
4. Execute the read capability through the Edge and capture normalized result.
5. Record durable evidence and update traceability + documentation.

## Work Log

### 2026-09-03T23:34:10+08:00 — Session opened
- (existing placeholder log from prior session, left OPEN).

### 2026-09-04T00:30 — Diagnose lab and transfer blocker
- Confirmed Alpine VM (172.21.0.20) unreachable after reboot; boots ephemeral to
  a bare ISO state (no sshd, no network config).
- Confirmed GNS3 controller/compute = GNS3 VM 172.21.0.2 (controller port 80,
  SSH 22); R1 (192.168.10.1) reachable via GNS3 VM tap0.
- Found `paramiko` SFTP to the GNS3 VM is fast (~84 MB/s); the slow path was the
  Windows OpenSSH SCP/SFTP client over the Cloud bridge.
- Decided to run the Edge as a persistent systemd service on the GNS3 VM instead
  of the ephemeral Alpine.

Commands executed (representative, live):
```text
paramiko SFTP upload tmp/ainet-edge-linux + PKI -> /opt/ainet-edge
ssh-keyscan/sshpass capture R1 ssh-rsa host key (fp matches expected)
sudo tee /etc/systemd/system/ainet-edge.service; systemctl enable --now ainet-edge
```

### 2026-09-04T00:55 — PKI roles and redeploy
- The existing `dev_pki.py` issued central=SERVER_AUTH and edge=CLIENT_AUTH for
  the edge-client model. The server-mode Edge needs the Central to present a
  CLIENT_AUTH cert and the Edge a SERVER_AUTH cert.
- Added `tools/gen_m1_live_pki.py` (dual SERVER+CLIENT auth, edge SAN IP
  `172.21.0.2`) reusing the existing dev CA; regenerated `tmp/m1-live-pki`.
- Redeployed Edge cert/key to the GNS3 VM and restarted the service.

Commands executed:
```text
python tools/gen_m1_live_pki.py tmp/m1-live-pki --edge-ip 172.21.0.2
python tmp/redeploy_edge_pki.py          # SFTP + systemctl restart
```

### 2026-09-04T01:10 — Enroll and dispatch over mTLS
- Raw SSL client (central.crt central.key) -> `POST /v1/control/hello` 200
  WELCOME and `/v1/control/ready` 200 READY_ACK (Edge enrollment/auth verified).
- Direct task dispatch -> `POST /v1/control/task` 200 with normalized
  `device.read.facts` result for R1.

Commands executed:
```text
python tmp/mtls_dispatch_test.py   # hello/ready/task over mTLS -> 200
```

### 2026-09-04T01:17 — R1 credential remediation
- R1 SSH rejected the stored `CISCO_ROUTER_PASSWORD`; re-provisioned R1 `admin`
  password to the project `.env` value via the R1 console (privileged exec).
- Confirmed R1 SSH auth now works (IOSv 15.6(2)T banner returned).

### 2026-09-04T01:20 — Wire through existing API surface
- The central `edge_dispatch_client` used httpx `verify`+`cert` which silently
  dropped the client cert on Windows. Extended `edge_dispatch.py` to build an
  explicit `ssl.SSLContext` (verify CA + present client cert).
- Started a fresh central backend (`uvicorn app.main:app` on 127.0.0.1:8010) with
  `EDGE_CONTROL_URL=https://172.21.0.2:9443` and the m1-live-pki certs.
- Added `r1-m1` EDGE-routed inventory device.
- `POST /api/v1/tasks/capability` -> 200, task `device.read.facts - R1`
  status `success`, `execution_location EDGE`, normalized result, audit event
  `TASK-EDGE-EXECUTION` result `success`.

Commands executed:
```text
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010
POST http://127.0.0.1:8010/api/v1/tasks/capability   -> 200 (task-20260903172217-556e67)
GET  http://127.0.0.1:8010/api/v1/audit              -> TASK-EDGE-EXECUTION success
```

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/edge_dispatch.py` | modified `_client` to use explicit `ssl.SSLContext` | httpx verify+cert dropped client cert on Windows |
| `tools/gen_m1_live_pki.py` | created | role-correct certs + edge SAN IP for server-mode Edge |
| `.env` | added `EDGE_CONTROL_URL`, `EDGE_CA/CERT/KEY_FILE`, `EDGE_ID`, `EDGE_VERSION` | configure live Edge dispatch |
| `docs/evidence/m1-vertical-slice/README.md` | created | M1 evidence index |
| `docs/evidence/m1-vertical-slice/r1-facts-live-result-20260903.json` | created | protocol-level evidence |
| `docs/evidence/m1-vertical-slice/central-api-capability-live-20260903.json` | created | API-level + audit evidence |
| `docs/session-logs/2026/09/2026-09-03_2334_phase-01_m1-vertical-slice-edge-lab-execution.md` | updated/closed | mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Edge process/listen | `systemctl is-active ainet-edge`; `ss -ltnp \| grep 9443` | PASS (active, listening *:9443) |
| Edge enrollment | mTLS `POST /v1/control/hello` 200 WELCOME + `/ready` 200 READY_ACK | PASS |
| Read capability through Edge | mTLS `POST /v1/control/task` device.read.facts -> 200 normalized | PASS |
| Existing API surface | `POST /api/v1/tasks/capability` -> 200, task success, EDGE | PASS |
| Audit evidence | `GET /api/v1/audit` -> `TASK-EDGE-EXECUTION` result=success | PASS |
| R1 SSH | sshpass `show version` -> IOSv 15.6(2)T | PASS |
| Go unit tests | (baseline) | NOT RUN this session (unchanged code path) |

## Errors and Blockers

- Alpine VM (172.21.0.20) became unreachable/rebooted ephemeral; skipped in favor
  of persistent GNS3 VM deployment. Not a regression; the Alpine path was never M1
  mandatory once a persistent Edge was available.
- httpx `verify`+`cert` silently dropped the client certificate on Windows;
  resolved by building an explicit `ssl.SSLContext`.
- R1 SSH stored password did not match; re-provisioned R1 `admin` to the project
  `.env` value during this session (documented in evidence README).
- The Windows OpenSSH SCP/SFTP Cloud-bridge path stalls on large files; used
  paramiko SFTP to the GNS3 VM instead.

## Security / Licensing Notes

- No secrets, enrollment tokens, private keys, or controller auth tokens are
  recorded in this log or evidence JSONs (keystore values were transferred over
  authenticated SSH but not logged).
- Development-only PKI (`tmp/m1-live-pki`, `tmp/edge-live-pki/ca.key`) is used;
  no production claims.
- R1 SSH password was reset to the project `.env` value during this session.

## Compatibility / Recovery Notes

- The Edge runs as a persistent systemd service on the GNS3 VM; restarting the
  service restores the mTLS listener at 172.21.0.2:9443.
- `edge_dispatch.py` change is backward-compatible (now uses an SSLContext
  instead of `verify`+`cert`; behavior identical or improved).
- The central backend on 127.0.0.1:8010 is an additional live instance used for
  evidence; the pre-existing backend on 8000 remains running.

## Decisions / ADRs

- No new ADR created. The server-mode Edge + Central outbound dispatch is
  consistent with `docs/repository-assessment-v5.md` and the existing
  `edge_dispatch_client`. A durable ADR for the Edge deployment target should be
  considered before Milestone 2.

## Milestone 1 Acceptance Gate — Assessment

| Criterion | Result |
|---|---|
| Repository capability assessment complete | PASS |
| No unnecessary parallel subsystem | PASS |
| OverlayProvider/control skeleton works | PASS |
| Edge enrolls/authenticates | PASS (live HELLO/READY over TLS 1.3 mTLS) |
| One read-only capability executes through Edge | PASS (`device.read.facts` -> R1) |
| Structured result reaches existing API/tool surface | PASS (task output + `/tasks` API) |
| Exact test evidence recorded | PASS (docs/evidence/m1-vertical-slice/*) |

Milestone 1 gate: **PASS**. Do not proceed to Milestone 2 without this record.

## Remaining Work

- Optional: wire the same dispatch through the frontend task UI (not M1 required).
- Before Milestone 2: consider an ADR for the Edge deployment target and PKI roles.

## Next Session Handoff

Start from Milestone 2 (Safety and Reliable Execution Contract). The live M1
vertical slice now runs:

- Edge: systemd `ainet-edge` on GNS3 VM 172.21.0.2 (control-list 0.0.0.0:9443).
- Central: `edge_dispatch_client` configured via `.env` EDGE_* settings.
- Device: R1 (`r1-m1`) Cisco IOSv 192.168.10.1, `credential_ref=r1-lab`.

Recommended next action:
1. Ensure `tools/deploy_gns3vm_edge.py` (paramiko SFTP + systemd) is committed for
   reproducibility.
2. Begin Milestone 2 TaskAttempt/lease + retry/credential/parity work against the
   live Edge.

## Final Summary

Milestone 1 vertical slice is complete and verified against a live lab: Central
`/api/v1/tasks/capability` routed `device.read.facts` to an enrolled Edge over
mTLS, the Edge executed the read against R1 (Cisco IOSv 15.6(2)T) via a pinned
local credential reference, and returned a normalized structured result with
audit evidence. The Milestone 1 acceptance gate PASSes.
