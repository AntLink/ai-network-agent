---
name: ai-network-agent-frontend
description: Build, extend, review, and maintain the AI Network Agent frontend using shadcndashboard as the base UI. Use for React/Vite/TypeScript/shadcn dashboard work involving devices, AI agent workflows, GNS3, Containerlab, vrnetlab, Cisco, MikroTik, Aruba, topology, terminal, configuration deployment, backups, alerts, audit logs, and network-automation safety.
compatibility: OpenCode V2; React 19; Vite; TypeScript; Tailwind CSS v4; shadcn-style components
metadata:
  opencode/autoinvoke: "true"
---

# AI Network Agent Frontend Skill

Use this skill when working on the frontend/UI of the **AI Network Agent** project based on:

- Base dashboard: `https://github.com/shadcndashboard/shadcndashboard`
- Target product: an **AI-powered Network Operations Center** for Cisco, MikroTik, Aruba, GNS3, Containerlab, and vrnetlab.

## Core rule

Do **not** turn the base dashboard into a generic CRUD admin panel.

The finished product must feel like a network operations and automation control center where users can:

- inspect network state,
- manage devices and labs,
- interact with an AI network agent,
- review execution plans,
- run dry-runs,
- approve configuration changes,
- observe streamed execution,
- validate post-change state,
- inspect backups and audit trails,
- recover safely from failed changes.

## Mandatory first step: repository discovery

Before editing code, inspect the actual repository. Never assume the layout only from this skill.

Read, if present:

1. `README.md`
2. `AGENTS.md`
3. `package.json`
4. `src/routes/Router.tsx`
5. `src/layouts/`
6. `src/components/`
7. `src/views/`
8. `src/api/`
9. `src/types/`
10. theme/provider code
11. existing dashboard pages
12. existing tables/forms/charts
13. MSW/SWR usage

Then summarize:

- current architecture,
- reusable components,
- route conventions,
- data-fetching conventions,
- styling conventions,
- gaps between the current repo and the requested feature.

Do not modify files until this discovery is complete.

Read `references/repo-conventions.md` before implementing routes, API mocks, charts, or layouts.
Read `references/frontend-blueprint.md` when planning or implementing product pages.
Read `references/network-safety-ux.md` before implementing configuration or destructive workflows.
Read `docs/AI_NETWORK_COPILOT_ARCHITECTURE.md` before implementing or changing `/agent`, `/tasks`, `/terminal`, configuration approval, or real-time event rendering.

## Preserve the base stack

Prefer the existing project stack and conventions:

- React + Vite
- TypeScript
- Tailwind CSS
- existing shadcn-style/Base UI components
- React Router conventions already used by the repo
- existing dark/light theme
- Recharts for charts
- Lucide/Iconify packages already present
- SWR for client fetching if used by the current repo
- MSW for mocks if used by the current repo

Do not add an overlapping UI framework, chart library, state-management library, or HTTP layer unless there is a concrete need and the existing stack cannot reasonably solve it.

## Architecture boundaries

The frontend must **never** directly perform SSH, Telnet, SNMP, Netmiko, Scrapli, NAPALM, GNS3 server shell access, or Containerlab host commands.

The browser talks only to backend APIs and real-time endpoints.

Preferred separation:

```text
UI components
    ↓
feature hooks / service functions
    ↓
API client layer
    ↓
Backend
    ↓
Network drivers / lab engines
```

Keep secrets out of localStorage, sessionStorage, query strings, logs, client bundles, and mock fixtures.

## Primary information architecture

Use the following navigation as the default product model unless the repository or user request requires a justified variation:

```text
Dashboard

AI
├── Agent
└── Tasks

Network
├── Devices
├── Topology
├── Discovery
└── Alerts

Labs
├── Labs
├── GNS3
└── Containerlab

Automation
├── Configurations
├── Backups
└── Audit Logs

System
├── Credentials
└── Settings
```

## Main routes

Prefer these routes:

```text
/dashboard
/agent
/tasks
/tasks/:id
/terminal
/devices
/devices/:id
/topology
/topology-builder
/discovery
/alerts
/labs
/labs/:id
/gns3
/containerlab
/configurations
/backups
/audit
/settings
/settings/credentials
```

Follow the repository's lazy-loading and route declaration pattern instead of introducing a second router structure.

## Dashboard priorities

The main dashboard should answer these questions immediately:

1. Is the network healthy?
2. Which devices or labs need attention?
3. What is the AI agent doing?
4. What recently changed?
5. Are backend services connected?

Recommended high-value dashboard blocks:

- Total Devices
- Online / Offline / Warning devices
- Active Labs
- AI Operations today
- Network Health
- Network Health trend chart
- Device Status table
- Recent AI operations
- Alerts requiring attention
- Backend/GNS3/Containerlab/AI provider connection status

Avoid decorative widgets that do not help network operations.

## AI Agent UX

The `/agent` page is a core product feature, not a generic chat box.

The composer should support, when backend capability exists:

- multiline prompt,
- device selector,
- lab selector,
- topology context,
- attachments,
- prompt history,
- Run,
- Dry Run,
- Plan Only.

Example requests:

- Configure OSPF between R1 and R2.
- Create VLAN 10 on all Aruba switches.
- Find why MikroTik R1 cannot reach the internet.
- Build site-to-site IPsec between Cisco routers.
- Create a Containerlab topology with two Cisco routers and one MikroTik.
- Back up all network devices.

Never present an AI-generated configuration as already applied unless the backend confirms successful execution.

The AI experience should behave as a Network Copilot:

```text
Plan -> Validate -> Execute -> Verify
```

The UI should render agent output as typed operational cards when backend data is available:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `alert`
- `verification`

Do not reduce every agent response to Markdown if the response contains structured state. Plans, approvals, diffs, command output, and verification results should use dedicated card layouts.

The frontend must not imply the LLM has direct SSH access. Show generated intent, plan, dry run, approval state, execution progress, and verification results. Backend drivers own the vendor-specific command translation.

## Network change workflow

Any AI or user-driven configuration change should be designed around this flow:

```text
User Request
    ↓
Agent Plan
    ↓
Collect Current State
    ↓
Generate Candidate Configuration
    ↓
Validate
    ↓
Dry Run / Diff
    ↓
User Approval (when required)
    ↓
Backup
    ↓
Deploy
    ↓
Post-check
    ↓
Success OR Rollback
```

The UI should make the current stage obvious.

For risky actions display:

- target devices,
- exact scope,
- candidate commands/config diff,
- risk level,
- management-connectivity impact,
- backup status,
- expected validation,
- rollback availability.

Read `references/network-safety-ux.md` for detailed rules.

## Cisco classic UI considerations

Do not model Cisco IOS classic as if every configuration operation is a one-line command like RouterOS.

Cisco may use hierarchical CLI states:

```text
R1>
R1#
R1(config)#
R1(config-if)#
R1(config-router)#
R1(config-crypto-map)#
```

The frontend should generally display:

- structured intent,
- generated candidate configuration,
- execution transcript,
- validation results,

rather than requiring the user to reason about internal prompt state.

## Device detail page

`/devices/:id` should normally have tabs such as:

- Overview
- Interfaces
- Routing
- Configuration
- Commands
- Backups
- Metrics
- Logs

Useful overview data:

- hostname
- vendor
- model/platform
- OS version
- management IP
- status
- uptime
- CPU
- memory
- connection status
- authentication method
- privilege information where applicable

Do not fake unsupported metrics. Show `Unavailable` or an explicit empty state.

## Terminal page

The terminal is for operational interaction and streaming output.

Useful controls:

- device selector
- connection status
- reconnect
- command history
- clear
- copy output
- save output
- fullscreen
- raw mode when supported
- "Explain with AI"

The terminal must consume a backend stream/API. Do not implement browser-side SSH.

## Topology

For interactive topology, prefer a mature React topology/graph library only if one is not already present.

Topology nodes should expose:

- hostname
- vendor
- status
- management IP when appropriate

Links should expose:

- endpoint A/interface
- endpoint B/interface
- operational status

Essential interactions:

- pan
- zoom
- fit view
- select node
- inspect device
- optionally drag layout positions

Avoid turning topology into a decorative diagram with no operational linkage.

## GNS3 / Containerlab / vrnetlab

Treat these as execution backends managed by the backend service.

GNS3 pages can show:

- controller status
- GNS3 VM status
- projects
- nodes
- start/stop actions

Containerlab pages can show:

- topology files
- deployed labs
- nodes
- images
- validate/deploy/destroy actions
- YAML editor when requested

vrnetlab should generally appear as image/runtime metadata associated with lab nodes rather than as a separate end-user management system unless the backend exposes explicit vrnetlab lifecycle features.

## API organization

Prefer feature-oriented API files, following current repository conventions. Example target shape:

```text
src/api/devices.ts
src/api/labs.ts
src/api/tasks.ts
src/api/agent.ts
src/api/gns3.ts
src/api/containerlab.ts
src/api/configurations.ts
```

If the repository uses a different pattern such as per-feature folders/handlers/data files, follow that instead.

Do not hardcode production backend URLs inside page components.

## Core TypeScript models

Create/reuse typed models for domain data. Typical entities:

- `Device`
- `NetworkInterface`
- `Route`
- `Lab`
- `TopologyNode`
- `TopologyLink`
- `Task`
- `TaskStep`
- `Alert`
- `AuditLog`
- `Backup`
- `Configuration`
- `ConfigurationDiff`
- `AgentMessage`
- `ExecutionPlan`
- `ConnectionStatus`

Use strict union values for vendor/status/severity fields where practical.

## Real-time readiness

Design terminal, agent execution, task progress, device state, and alerts so they can consume SSE/WebSocket streams.

Expected event concepts may include:

```text
device_status
task_update
command_output
agent_message
alert_created
topology_change
```

Agent/task event payloads may include card-level types such as:

```json
{
  "type": "task_progress",
  "task_id": "task-182",
  "step": "backup",
  "status": "success",
  "message": "Running configuration backed up"
}
```

Render these events as progress state, not as raw JSON, except in a debug/raw view.

Do not build a fake polling architecture that makes future streaming unnecessarily difficult if the backend requirements clearly call for streaming.

## Required UI states

Every data-driven page must handle:

- loading
- empty
- error
- success
- stale/reconnecting when applicable

Tables should remain usable on narrower screens with intentional responsive behavior or horizontal scrolling.

Desktop network-operations use is the priority, but the shell must remain responsive.

## Mock data

When the backend is not ready, use the repository's existing mock mechanism rather than hardcoded arrays inside page components.

Use realistic examples, such as:

```text
R1     Cisco     IOSv     Online
R2     Cisco     IOSv     Online
MT-R1  MikroTik  CHR      Online
SW1    Aruba     AOS-CX   Warning
```

Mocks must never contain real credentials, tokens, keys, or personal secrets.

## Implementation phases

Do not attempt the whole application in one uncontrolled change.

### Phase 1 — Foundation

- repository analysis
- sidebar/navigation
- dashboard
- devices
- device detail

### Phase 2 — AI operations

- AI Agent
- execution plan
- tasks
- terminal

### Phase 3 — Lab control

- labs
- topology
- GNS3
- Containerlab

### Phase 4 — Automation governance

- configurations
- backups
- alerts
- audit logs

### Phase 5 — Administration

- settings
- credentials
- discovery

If the user asks for only one feature, implement only the smallest required phase/slice.

## Validation gates

Before declaring a frontend change complete, run the repository's actual validation commands. For the shadcndashboard base these commonly include:

```bash
npm run lint
npm run build
```

Do not declare success with TypeScript errors, lint failures, broken imports, invalid routes, or obvious runtime failures.

If tests exist, run the relevant tests too.

## Change discipline

- Reuse before creating new components.
- Avoid unnecessary dependencies.
- Do not rewrite the entire design system.
- Do not move unrelated files.
- Keep changes scoped.
- Follow existing naming conventions.
- Preserve dark mode.
- Preserve responsive behavior.
- Keep network-specific business logic out of presentational components.
- Explain architectural deviations when they are necessary.

## Review mode

When asked to review this frontend, inspect:

- route integrity
- reusable component quality
- TypeScript correctness
- API/data-flow boundaries
- security of credential handling
- loading/error/empty states
- real-time architecture
- destructive-action safeguards
- accessibility
- responsive behavior
- dark mode
- dependency duplication
- mock/backend separation
- network-domain correctness

Classify meaningful findings as:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFO

For each issue, identify the actual file/component and recommend a concrete fix.

## Definition of done

The result should feel like an **AI-powered Network Operations Center**, not a themed admin template.

A network engineer should be able to understand:

- device health,
- lab health,
- topology,
- AI activity,
- planned changes,
- active execution,
- failures,
- configuration history,
- rollback state,
- and system connectivity

from one coherent application.
