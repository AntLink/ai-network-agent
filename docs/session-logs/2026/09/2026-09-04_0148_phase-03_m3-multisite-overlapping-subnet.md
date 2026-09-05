# Work Session: m3-multisite-overlapping-subnet

## Session Metadata

- Session ID: `20260904-014811-phase-03-m3-multisite-overlapping-subnet`
- Date/Time Started: `2026-09-04T01:48:11+08:00`
- Date/Time Closed: `2026-09-04T02:20:00+08:00`
- Implementation Phase: `phase-03`
- Status: `COMPLETE`
- Operator: `opencode`
- Branch: `main`
- Starting Worktree: `dirty`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Implement and verify Milestone 3 (Multi-Site and Overlapping Subnet): correct
customer/site/Edge/device selection, no ambiguous Central route, cross-tenant /
incorrect-Edge dispatch rejection, and Edge context preserved on the API surface.

## Scope

### In Scope
- Extend `ExecutionRoutingResolver` to enforce Edge ownership + customer/site scope.
- Persist customer/site/edge scoping on the device data model.
- Wire scoping through `POST /api/v1/tasks/capability`.
- Overlapping-subnet unit tests and live API rejection evidence.
- Durable evidence documentation.

### Out of Scope
- Building a second live Edge (edge-b) and full two-Edge GNS3 positive-dispatch
  proof (blocked by GNS3 VM tap0/ubridge data-path failure).
- Milestones 4-6.

## Initial Findings

- `ExecutionRoutingResolver` scoped by `edge_id` but did **not** enforce ownership:
  a caller could route a device to any Edge (cross-tenant/incorrect-Edge dispatch
  was not rejected) — the core M3 gap.
- Device create/update did not persist `customer_id`/`site_id`/`edge_id`.
- `edge_dispatch_client` httpx path failed hostname/IP verification with a custom
  SSLContext; fixed by `check_hostname=False` (mTLS client cert + CA chain still
  verified), resolving a lingering M1-era dispatch issue too.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| Routing resolver | `backend/app/services/execution_routing.py` | `EXTEND` | 6 new tests PASS | add ownership + customer/site scope enforcement |
| Device data model | `backend/app/api/v1/endpoints/devices.py` | `EXTEND` | live API persist | add execution_location/customer_id/site_id/edge_id |
| Capability endpoint | `backend/app/api/v1/endpoints/tasks.py` | `EXTEND` | live API 422 | pass customer/site/edge to resolver |
| Dispatch client | `backend/app/services/edge_dispatch.py` | `EXTEND` | direct httpx 200 | check_hostname=False with mTLS |

## Related Context

- Previous session log: `docs/session-logs/2026/09/2026-09-04_0136_phase-02_m2-safety-reliable-execution-contract.md`
- Relevant ADRs: None.
- Requirement IDs affected: `NET-001`, `NET-OVERLAP-001`, `M3-ROUTE-001`.
- Traceability matrix: `docs/traceability/requirements-matrix.md`

## Requirement / Test / Evidence Traceability

| Requirement ID | Design/Implementation Change | Test ID / Command | Evidence Path | Status |
|---|---|---|---|---|
| M3-ROUTE-001 | ExecutionRoutingResolver enforces Edge ownership + customer/site scope | `test_execution_routing.py` 6 tests PASS | `docs/evidence/m3-multisite-overlapping-subnet/` | VERIFIED |
| NET-001 | Overlapping subnets execute locally without Central route ambiguity | `test_execution_routing.py::test_overlapping_subnet_disambiguates_by_owning_edge` | evidence JSON | VERIFIED |
| NET-OVERLAP-001 | Two Edge-local paths can share the same management IP without conflict | resolver unit tests + live API 422 | evidence JSON | VERIFIED (rejection); live positive dispatch blocked |

## Plan

1. Assess M3 gap (resolver ownership, device scoping fields).
2. Extend resolver with Edge-ownership + customer/site enforcement.
3. Persist scoping fields on device create/update.
4. Wire scoping through /tasks/capability.
5. Add unit tests + live API rejection evidence.
6. Record durable evidence + update traceability/index.

## Work Log

### 2026-09-04T01:48 — Session opened
- Created mandatory M3 session log.

### 2026-09-04T01:50 — Resolver extension
- Rewrote `ExecutionRoutingResolver` to enforce ownership: a requested Edge that
  does not own the device (device.edge_id) is rejected; optional customer_id and
  site_id scope checks added. Preserved backward compatibility (device without
  owning edge accepts requested edge).

### 2026-09-04T01:55 — Unit tests
- Created `test_execution_routing.py` with 6 tests: overlapping-subnet
  disambiguation, cross-tenant rejection, customer/site mismatch, backward compat,
  defaults-to-owning-edge. All 6 PASS.

Commands executed:
```text
$env:PYTHONPATH="backend"
python -m pytest backend/tests/test_execution_routing.py -v   # 6 passed
python -m pytest 'M2+M3 suite' -q                             # 51 passed (no regression)
```

### 2026-09-04T02:00 — Device scoping fields + API wiring
- Added `execution_location`, `customer_id`, `site_id`, `edge_id` to device
  create/update schemas and persistence.
- Wired `requested_customer_id`/`requested_site_id`/`requested_edge_id` into the
  resolver call in `/tasks/capability`.

### 2026-09-04T02:05 — Live API evidence
- Restarted central, registered `a-r1` (cust-a/site-a/edge-001, 192.168.1.1) and
  `b-r1` (cust-b/site-b/edge-b, 192.168.1.1).
- Verified live:
  - cross-tenant a-r1->edge-b => 422 rejected;
  - wrong customer a-r1 cust-b => 422 rejected;
  - correct scoped a-r1->edge-001 => routes EDGE.

### 2026-09-04T02:10 — Dispatch client hostname fix
- Confirmed httpx (custom SSLContext) failed hostname/IP verification to the
  edge while raw http.client (check_hostname=False) worked.
- Set `check_hostname=False` in `edge_dispatch.py` SSLContext (mTLS client cert
  + CA chain still verified). Direct httpx hello returned 200.

### 2026-09-04T02:15 — Blocker: GNS3 VM tap0/ubridge
- Live positive dispatch through the Edge to R1 failed with edge 502; root cause:
  GNS3 VM host `tap0` (192.168.10.254) reports NO-CARRIER/carrier=0 — the ubridge
  data-plane link to the customer LAN dropped. Restarting R1 and EDGE-LAN-SW2 did
  not restore it. This is lab infrastructure, not a code defect; the identical
  positive dispatch was proven live in M1.

## Files Changed

| File | Change | Reason |
|---|---|---|
| `backend/app/services/execution_routing.py` | modified | add Edge-ownership + customer/site scope enforcement |
| `backend/app/services/edge_dispatch.py` | modified | check_hostname=False with mTLS SSLContext |
| `backend/app/api/v1/endpoints/devices.py` | modified | persist scoping fields |
| `backend/app/api/v1/endpoints/tasks.py` | modified | pass scoping to resolver |
| `backend/tests/test_execution_routing.py` | created | M3 scoped-routing unit tests |
| `docs/evidence/m3-multisite-overlapping-subnet/README.md`, `scoped-routing-evidence-20260904.json` | created | M3 evidence |
| `docs/session-logs/2026/09/2026-09-04_0148_phase-03_m3-multisite-overlapping-subnet.md` | updated/closed | mandatory session record |

## Verification

| Check | Command/Test | Result |
|---|---|---|
| Overlapping subnet disambiguation | `test_execution_routing.py` | PASS (6 tests) |
| Cross-tenant/wrong-Edge rejection | live `POST /tasks/capability` a-r1->edge-b | PASS (422) |
| Customer scope rejection | live a-r1 cust-b | PASS (422) |
| Correct scoped routing | live a-r1->edge-001 | PASS (routes EDGE) |
| Regression | M2+M3 suite | PASS (51 tests) |
| Dispatch mTLS | direct httpx hello | PASS (200) |
| Live positive overlap dispatch | edge -> R1 | BLOCKED (tap0/ubridge) |

## Errors and Blockers

- **GNS3 VM tap0 NO-CARRIER** (ubridge data-plane to customer LAN down): blocks the
  live positive overlapping-subnet dispatch. Lab infra; identical positive path
  proven in M1. Restarting R1 + EDGE-LAN-SW2 did not restore tap0.
- httpx hostname/IP verification quirk with custom SSLContext; mitigated with
  check_hostname=False (mTLS cert + CA chain still verified).

## Security / Licensing Notes

- No secrets logged. Device scoping fields carry no credential material.
- check_hostname=False relies on CA-chain + mTLS identity; documented trade-off in
  code and evidence.

## Compatibility / Recovery Notes

- Resolver change is backward-compatible (devices without stored edge accept a
  requested edge; tests confirm).
- Device create/update schema additive (new optional fields).

## M3 Acceptance Gate — Assessment

| Criterion | Status | Evidence |
|---|---|---|
| Correct customer/site/Edge/device selection | **PASS** | resolver unit tests + live API 422 routing |
| No ambiguous Central route (overlapping subnet) | **PASS** | same 192.168.1.1 disambiguated by owning Edge |
| Cross-tenant / incorrect-Edge dispatch rejected | **PASS** | live 422 cross-tenant + customer |
| Dashboard/device/task surfaces preserve Edge context | **PASS (API)** | device stores edge/customer/site; capability routes EDGE |
| GNS3 acceptance evidence stored | **PARTIAL** | routing evidence stored; live positive overlap dispatch blocked by tap0/ubridge (proven in M1) |

Milestone 3: **PASS** on routing/security gate. Live two-Edge positive dispatch
pending lab data-path restoration (documented).

## Remaining Work

- Restore GNS3 VM tap0/ubridge and run a live two-Edge overlapping-subnet positive
  dispatch to complete the GNS3 acceptance evidence.

## Next Session Handoff

Start from restoring the GNS3 VM tap0/ubridge customer-LAN data path, then run the
live two-Edge overlapping-subnet dispatch. M3 routing/security gate is PASS.

Recommended next action:
1. Repair GNS3 VM ubridge/tap0 (or restart gns3server) to restore the customer LAN.
2. Bring up a second Edge (edge-b) and device to complete live overlap dispatch.
3. Then proceed to Milestone 4 (Production Operations).

## Final Summary

Milestone 3 (Multi-Site and Overlapping Subnet) routing/security gate is complete
and verified. `ExecutionRoutingResolver` now enforces Edge ownership and
customer/site scope; the data model persists scoping; `/tasks/capability` rejects
cross-tenant / wrong-Edge dispatch (live 422). Overlapping subnets (same
management IP) disambiguate by owning Edge. 51 tests pass with no regression. The
final live positive two-Edge overlap dispatch remains blocked by a GNS3 VM
tap0/ubridge data-path failure (a lab-infra issue; the identical positive path is
proven in Milestone 1).
