---
name: agent-frontend-structure
description: Plan or implement the `/agent` frontend file structure for AI Network Agent, including shell layout, assistant-ui chat, session handling, message renderers, API layer, and shared agent types.
---

# Agent Frontend Structure

Use this skill when splitting or implementing the `/agent` frontend in `ai-network-agent`.

The goal is to keep the page readable and maintainable by separating:

- page shell and layout
- chat runtime and assistant-ui components
- session management
- message renderers
- API service layer
- shared frontend types
- small helper logic

## Preserve Existing Pattern

Keep the current Vite + React + TypeScript + Tailwind + shadcn/Base UI setup.

Do not replace the dashboard design system.
Do not move network or SSH logic into the browser.
Do not hardcode backend behavior inside page components.

Keep these existing entry points as the base:

- `src/views/agent/index.tsx`
- `src/components/assistant-ui/index.tsx`
- `src/components/assistant-ui/thread.tsx`
- `src/components/assistant-ui/chat-adapter.ts`
- `src/components/assistant-ui/session-list.tsx`
- `src/api/agent.ts`

## Recommended Frontend Structure

```text
src/
├─ views/
│  └─ agent/
│     ├─ index.tsx
│     ├─ agent-shell.tsx
│     ├─ agent-layout.tsx
│     ├─ agent-header.tsx
│     ├─ agent-empty-state.tsx
│     ├─ agent-loading-state.tsx
│     └─ agent-error-state.tsx
│
├─ components/
│  ├─ assistant-ui/
│  │  ├─ index.tsx
│  │  ├─ chat-adapter.ts
│  │  ├─ thread.tsx
│  │  ├─ session-list.tsx
│  │  ├─ session-toolbar.tsx
│  │  ├─ composer.tsx
│  │  ├─ device-selector.tsx
│  │  ├─ lab-selector.tsx
│  │  ├─ safety-mode-switcher.tsx
│  │  ├─ attachment-picker.tsx
│  │  ├─ connection-status-bar.tsx
│  │  ├─ message-renderers/
│  │  │  ├─ index.ts
│  │  │  ├─ message-card.tsx
│  │  │  ├─ plan-card.tsx
│  │  │  ├─ device-state-card.tsx
│  │  │  ├─ command-output-card.tsx
│  │  │  ├─ approval-card.tsx
│  │  │  ├─ task-progress-card.tsx
│  │  │  ├─ verification-card.tsx
│  │  │  ├─ alert-card.tsx
│  │  │  └─ config-diff-card.tsx
│  │  ├─ panels/
│  │  │  ├─ index.ts
│  │  │  ├─ session-panel.tsx
│  │  │  ├─ execution-plan-panel.tsx
│  │  │  ├─ device-context-panel.tsx
│  │  │  ├─ risk-panel.tsx
│  │  │  └─ backend-status-panel.tsx
│  │  └─ hooks/
│  │     ├─ use-agent-sessions.ts
│  │     ├─ use-agent-session.ts
│  │     ├─ use-agent-context.ts
│  │     ├─ use-agent-stream.ts
│  │     └─ use-agent-actions.ts
│  │
│  └─ agent/
│     ├─ execution-plan-card.tsx
│     ├─ agent-status-badge.tsx
│     ├─ risk-badge.tsx
│     ├─ approval-actions.tsx
│     └─ backend-health-badges.tsx
│
├─ api/
│  ├─ agent.ts
│  ├─ devices.ts
│  ├─ labs.ts
│  ├─ tasks.ts
│  ├─ alerts.ts
│  ├─ audit.ts
│  ├─ configurations.ts
│  ├─ backups.ts
│  ├─ discovery.ts
│  ├─ gns3.ts
│  ├─ containerlab.ts
│  └─ network/
│     └─ backend-client.ts
│
├─ types/
│  ├─ agent.ts
│  ├─ device.ts
│  ├─ lab.ts
│  ├─ task.ts
│  ├─ alert.ts
│  ├─ audit.ts
│  ├─ backup.ts
│  ├─ configuration.ts
│  ├─ stream.ts
│  └─ topology.ts
│
└─ lib/
   └─ agent/
      ├─ session-store.ts
      ├─ message-parser.ts
      ├─ plan-utils.ts
      ├─ risk-evaluator.ts
      ├─ safety.ts
      └─ formatters.ts
```

## How To Split Responsibilities

### `views/agent`

Keep page composition only.

- load initial state
- wire layout sections
- pass props to agent components
- handle loading and error states

Do not put streaming parsing or message rendering logic here.

### `components/assistant-ui`

Keep all chat-specific UI here.

- thread rendering
- session sidebar
- composer
- selectors
- attachment controls
- message cards
- right-side context panels

### `api`

Keep all backend requests here.

- session CRUD
- message CRUD
- plan requests
- task progress
- device/lab context
- configuration preview
- backup and audit lookup

### `types`

Keep the data contract here.

- session
- message
- plan
- device
- lab
- task
- alert
- audit
- stream event

### `lib/agent`

Keep reusable helper logic here.

- parse backend events
- normalize message types
- format plan data
- apply UI safety rules
- compute risk labels

## Implementation Order

When implementing the frontend split, use this order:

1. `types/agent.ts`
2. `api/agent.ts`
3. `components/assistant-ui/session-list.tsx`
4. `components/assistant-ui/message-renderers/*`
5. `components/assistant-ui/composer.tsx`
6. `components/assistant-ui/thread.tsx`
7. `views/agent/agent-shell.tsx`
8. `views/agent/index.tsx`
9. `lib/agent/*`

## Constraints

- Do not let the browser talk directly to SSH or LLM providers.
- Do not store credentials in browser storage.
- Do not render backend JSON as the default assistant response.
- Do not make destructive actions available without approval UI.
- Keep loading, empty, error, and streaming states in every visible part of `/agent`.

## Quality Target

The result should feel like a network copilot workspace, not a generic chat page.

The UI must support:

- resumable sessions
- device and lab context
- structured cards for plan/state/output
- approval gating
- backend streaming
- dark mode readability

