# AI Network Agent Phase Migration Draft

Date: 2026-08-26

## Goal

Refactor the current network dashboard into a project-aware, environment-aware AI Network Operations workflow without rewriting the entire application.

## Scope

This draft covers the full migration path from foundation to stabilization:

1. Phase 1 - Foundation
2. Phase 2 - Agent Core
3. Phase 3 - Environment Layer
4. Phase 4 - Deploy and Verify
5. Phase 5 - Stabilization

## Assumptions

- Existing React + Vite + TypeScript + Tailwind stack remains the base.
- Existing backend FastAPI modules remain the base.
- No hard rewrite of the current dashboard or router.
- `project_id` is the primary context key for all network operations.
- Lab, staging, and production are workflow layers, not separate applications.

## Phase Plan

### Phase 1 - Foundation

- Add environment and inventory types.
- Split `src/api/network` into domain-specific facades.
- Add `src/api/environments` and `src/api/inventory`.
- Keep current routes working while introducing the new context model.

### Phase 2 - Agent Core

- Move agent API into a dedicated module.
- Expand streaming/session types.
- Update assistant UI to render plan, approval, device state, and progress cards.
- Make agent responses project-aware.

### Phase 3 - Environment Layer

- Add lab, staging, and production views.
- Add environment switcher and workflow badges.
- Introduce approval and backup policy per environment.

### Phase 4 - Deploy and Verify

- Add deploy, dry-run, verify, and rollback service boundaries.
- Tie task progress to environment and project context.
- Strengthen audit trail metadata.

### Phase 5 - Stabilization

- Refactor oversized components into smaller reusable pieces.
- Update router, sidebar, and header to expose the new workflow.
- Ensure mock/live switching remains predictable.

## File Strategy

- Keep existing stable pages and layouts.
- Move only domain logic that is too broad.
- Add new modules for environment, inventory, deploy, and audit.
- Preserve compatibility facades while migration is in progress.

## Validation Gate

Each phase should end with:

- `npm run lint`
- `npm run build`

## Notes

- Topology and GNS3 handling should remain project-aware.
- Inventory must be able to work with both saved snapshots and live backend data.
- Production actions must remain approval-gated and backup-first.

## Phase 4 Implementation Note

Completed on 2026-08-26:

- Added backend task lifecycle helpers for seeded history, step tracking, SSE broadcast, and detailed task retrieval.
- Wired configuration apply to create deploy tasks, emit progress steps, and return task metadata.
- Wired rollback to create rollback tasks and broadcast completion state.
- Updated frontend Configurations page to show dry-run, workflow state, live task feed, and rollback action.
- Updated Tasks page to subscribe to task SSE, refresh live, and render detail timelines from backend task payloads.
- Validation passed with `npm.cmd run lint` and `npm.cmd run build`.
