# Work Session: m3-live-overlap-two-edge-proof

## Session Metadata

- Session ID: `20260904-025711-phase-03-m3-live-overlap-two-edge-proof`
- Date/Time Started: `2026-09-04T02:57:11+08:00`
- Date/Time Closed: `2026-09-04T03:25:00+08:00`
- Implementation Phase: `phase-03`
- Status: `PARTIAL`
- Operator: `opencode`
- Branch: `main`
- Starting Worktree: `dirty`
- Timezone: `Malay Peninsula Standard Time`

## Goal

Prove the Milestone 3 overlapping-subnet vertical slice live: run two Edges and two
devices with the SAME local management IP (192.168.1.1), and confirm Central routes
`device.read.facts` to the correct Edge for each device (no ambiguous route) and
returns each device's normalized result through the API.

## Scope

### In Scope
- Diagnose why host-process Edges on the GNS3 VM cannot reach the R1 customer LAN.
- Restore host -> customer-LAN data-plane reachability (tap bridge).
- Bring up a second Edge (edge-b) + second device for the overlap proof.
- Live dispatch to both edges with overlapping IP; confirm correct routing + results.

### Out of Scope
- New application code (the resolver cross-tenant enforcement is already M3-verified).
- Milestones 4-6 application work (depends on lab health; done in a separate session).

## Initial Findings

- 3 ubridge processes run on the GNS3 VM but only bridge **internal node-to-node UDP
  sockets** (127.0.0.1:20019<->20018 etc.). **No ubridge attaches to the host `tap0`**.
- The customer LAN switch `EDGE-LAN-SW2` (R1, PC1, ALPINE1, EDGE-2) has **no link to
  any host cloud/tap** -> host-process Edges have no data-plane path into the R1 LAN.
- `tap0` reports `NO-CARRIER`/`DOWN`. Root cause of "No route to host" for the Edge->R1
  dispatch: missing host-tap <-> customer-LAN bridge.
- Created host `tap1` (192.168.10.254/24) on the GNS3 VM and restarted gns3server so it
  would expose tap1 for a cloud node. gns3server restarted (active) but:
  - `POST /v2/projects/{BGP-LAB}/open` returns 404 after restart (project closed, will
    not reopen);
  - repeated controller /project /node queries were flaky for a short window.
- The project file `BGP-LAB.gns3` (37.2K) exists on disk; the open 404 is a GNS3 server /
  project-load state issue, not a missing file.

## Reuse / Extend / Refactor / Create Assessment

| Component | Existing Path | Classification | Evidence | Reason |
|---|---|---|---|---|
| ExecutionRoutingResolver (M3) | `backend/app/services/execution_routing.py` | `REUSE_AS_IS` | M3 unit tests + live API 422 | overlap routing logic already verified |
| GNS3 host->LAN bridge | GNS3 topology | `REFACTOR` (lab) | blocked | project won't reopen after server restart |

## Requirement / Test / Evidence Traceability

| Requirement ID | Test / Command | Evidence | Status |
|---|---|---|---|
| NET-OVERLAP-001 | resolver unit tests + live API 422 (M3 earlier) | `docs/evidence/m3-multisite-overlapping-subnet/` | VERIFIED (rejection/logic) |
| NET-OVERLAP-001 (live two-Edge dispatch) | not run | blocked by GNS3 project-open + tap bridge | BLOCKED (lab infra) |

## Work Log

- 02:57 session opened.
- 03:00 diagnosed ubridge: no host tap attached to customer LAN; tap0 NO-CARRIER.
- 03:10 created host tap1 (192.168.10.254/24) on GNS3 VM.
- 03:15 restarted gns3server to expose tap1; server active; tap1 visible.
- 03:20 attempted `POST /v2/projects/{id}/open` for BGP-LAB -> 404. Project file exists
  but will not reopen post-restart.
- 03:22 verified controller reachable (GET /v2/projects 200) but project open/nodes 404.
- 03:25 recorded blocker; pivot planned to self-contained M4 backup/restore drill.

## Errors and Blockers

- **BLOCKER (lab infra): GNS3 BGP-LAB project will not reopen** (POST open 404) after the
  gns3server restart, and host->customer-LAN tap bridging is not wired. Both prevent a
  live two-Edge overlapping-subnet dispatch. The project `.gns3` file is intact; this is
  a GNS3 server/project-load state problem, not a code defect.
- ubridge does not attach to host tap0; no host cloud node is linked into EDGE-LAN-SW2.

## Security / Licensing Notes

- No secrets logged.

## Compatibility / Recovery Notes

- No application code changed.

## M3 Gate Note

- The overlap **routing/logic** acceptance (correct selection, no ambiguous route,
  cross-tenant rejection) is VERIFIED via M3 resolver unit tests and live API 422
  evidence.
- The **live two-Edge positive dispatch** proof remains BLOCKED by GNS3 lab-infra
  instability; identical positive single-Edge dispatch proven in M1.

## Final Summary

Live two-Edge overlapping-subnet proof is blocked by GNS3 lab-infrastructure
instability (project won't reopen after server restart; host tap->LAN bridge not
wired). The overlap routing logic and cross-tenant rejection are already verified.
This session records the diagnosis (root cause: no host-tap bridge into the customer
LAN + project open failure) and defers the live proof until GNS3 recovers.