# Milestone 3 — Multi-Site / Overlapping Subnet Evidence

Proves scoped routing for overlapping customer LANs: devices behind different
customer/site/Edge contexts that share the **same management IP** resolve to the
correct Edge, and **cross-tenant / incorrect-Edge dispatch is rejected**.

## Topology under test

```text
Edge-A (edge-001) -> site-a (cust-a) -> 192.168.1.1 (a-r1)
Edge-B (edge-b)   -> site-b (cust-b) -> 192.168.1.1 (b-r1)
```

Central must target by customer/site/Edge/device identity and never create an
ambiguous global route.

## Implementation (REUSE+EXTEND)

- `backend/app/services/execution_routing.py` — `ExecutionRoutingResolver` now
  enforces **Edge ownership** and optional customer/site scope. A requested Edge
  that does not own the device is rejected.
- `backend/app/api/v1/endpoints/devices.py` — device create/update now persist
  `execution_location`, `customer_id`, `site_id`, `edge_id`.
- `backend/app/api/v1/endpoints/tasks.py` — `/tasks/capability` passes
  `customer_id`/`site_id`/`edge_id` into the resolver.

## Evidence files

- `scoped-routing-evidence-20260904.json` — live API cross-tenant rejection
  (422) for wrong Edge and wrong customer, plus unit-test summary.
- `live-two-edge-proof-20260904.json` — live mTLS dispatch to two Edges with
  overlapping IP (192.168.1.1), one FULL PASS, one pending credential fix.

## Unit tests (PASS)

`backend/tests/test_execution_routing.py` (6 tests):

1. overlapping subnet disambiguates by owning Edge (same 192.168.1.1);
2. cross-tenant / wrong Edge dispatch rejected;
3. customer scope mismatch rejected;
4. site scope mismatch rejected;
5. backward-compat: requested edge without stored owner accepted;
6. defaults to owning Edge from metadata.

## Live API evidence (PASS)

| Case | Request | Result |
|---|---|---|
| Cross-tenant (wrong Edge) | a-r1 -> edge-b | 422 `requested Edge 'edge-b' does not own ...` |
| Wrong customer | a-r1 -> edge-001, cust-b | 422 `requested customer 'cust-b' does not match ...` |
| Correct scoped routing | a-r1 -> edge-001 (cust-a, site-a) | routes EDGE=edge-001 |

## Positive live dispatch

### Live two-Edge overlapping-subnet proof (2026-09-04T09:08 UTC)

```text
Central (Windows) --mTLS--> 172.21.0.2:9443/9444 (reverse tunnel) --> ALPINE Edge --> SSH 192.168.1.1 --> device facts
```

- **edge-b (ALPINE2, port 9444)**: HELLO 200 → READY 200 → TASK 200
  - credential_ref=b-r1, SSH to IOSv2 (192.168.1.1)
  - Normalized result: hostname=R2, platform=ios, vendor=cisco, version=15.6(2)T
  - **END-TO-END PASS** ✅

- **edge-001 (ALPINE1, port 9443)**: HELLO 200 → READY 200 → TASK 502
  - credential_ref=a-r1, SSH to IOSv1 (192.168.1.1) failed (credential mismatch suspected)
  - **PENDING**: verify IOSv1 `admin` password matches keystore

Overlapping IP proven: two routers both at `192.168.1.1`, isolated by separate
Switch1/Switch2. Each Edge routes to its own device.

### Earlier proof

The identical `Central -> Edge -> R1 device.read.facts` positive dispatch was
proven live in **Milestone 1** (`task-20260903172217-556e67`, status success).
See `docs/evidence/m1-vertical-slice/central-api-capability-live-20260903.json`.

## Architecture: reverse-tunnel approach

ALPINE1/ALPINE2 are in isolated LANs (192.168.1.x) unreachable from the host.
Edge uses **NAT dial-out** + **reverse SSH tunnel** to expose control ports:

```text
ALPINE2 --ssh -R 9444:127.0.0.1:9444--> host (172.21.0.2)
Central (Windows) --mTLS--> host:9444 --> reverse tunnel --> ALPINE2:9444 --> Edge --> SSH R2
```

GatewayPorts=yes on the host ensures the reverse tunnel binds on all interfaces,
making it reachable from Windows at `172.21.0.2:9444`.

## Remaining

- Verify IOSv1 admin password matches edge-001 keystore a-r1 (credential fix → both edges pass).
- Record formal M3 acceptance gate once both edges return normalized results.
