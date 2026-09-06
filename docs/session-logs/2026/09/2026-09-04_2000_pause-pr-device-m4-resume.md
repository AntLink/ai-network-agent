# Work Session: m4-prod-ops-onward + PR-device-real

## Session Metadata

- Session ID: `20260904-200000-pause-pr-and-m4-resume`
- Date/Time Started: `2026-09-04T20:00:00+08:00`
- Date/Time Closed: `2026-09-04T20:05:00+08:00`
- Implementation Phase: `phase-04`
- Status: `CHECKPOINT`
- Operator: `opencode`
- Branch: `main`

## Purpose

Capture the pending PR (perangkat asli real-device testing) and reset the working
focus to Milestone 4 (Production Operations) per user request. No application code
changed in this checkpoint.

## Saved PR / Future Work (device-real validation)

Rencana disimpan untuk dikerjakan nanti (bukan sekarang):

- Arsitektur: Central di Windows PC, Edge di Laptop, Router MikroTik sebagai device asli.
- Jalur: Windows(laptop) --LAN--> Laptop(Edge host) --LAN--> MikroTik(device).
- Goal 1: buktikan full pipeline real `device.read.facts` terhadap MikroTik (gantikan GNS3
  yang rapuh). Ini bukti live paling meyakinkan untuk produksi.
- Goal 2 (opsional, M3 overlap real): 2 Edge + 2 device IP-sama untuk buktikan overlap
  routing secara stabil (routing logic sudah VERIFIED via unit + 422; tinggal bukti real).

## Milestone Status Snapshot (sebagai konteks lanjut)

- M1 Vertical Slice: PASS (live).
- M2 Safety/Reliability: PASS (45 Python + 5 Go tests).
- M3 Overlap routing: VERIFIED (unit + live 422 cross-tenant; edge-b FULL LIVE PASS).
- M4 Production Ops: PARTIAL — in progress (this milestone).
- M5 Scale/HA: PARTIAL (Redis resilience VERIFIED; live failover pending).
- M6 Private infra/Launch: not started.
- Total tests: 84 PASS.

## Next Work (this session onward)

Milestone 4 (Production Operations) remaining items:
- Edge install/deploy endpoint + signed release (canary/rollback) — core verified; endpoint pending.
- Backup/restore drill DB/controller/PKI (DR-001) — config restore planning verified; full drill pending.
- Monitoring collector/poller + persistence + notification.
- Operational readiness items.

## Handoff

Resume milestone-driven: next immediate slice = complete M4 acceptance items, then M5, M6 + launch gate.
