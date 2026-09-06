---
name: assistant-ui-backend-contract
description: Define and keep in sync the backend API contract for assistant-ui in the AI Network Agent dashboard, including sessions, messages, streaming events, attachments, agent plans, and typed operational cards.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Backend Contract

Use this skill when the task is about frontend-backend alignment for `/agent`.

## Contract focus

- Session CRUD.
- Message CRUD.
- Stream events.
- Attachment metadata.
- Device and lab selectors.
- Structured assistant response cards.

## Recommended schema

Session:

```ts
interface AgentSession {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  deviceIds: string[]
  labId?: string
  status: "idle" | "running" | "error"
}
```

Message:

```ts
interface AgentMessage {
  id: string
  sessionId: string
  role: "user" | "assistant" | "system" | "tool"
  content: string
  createdAt: string
  type?: "message" | "plan" | "device_state" | "command_output" | "config_diff" | "approval" | "task_progress" | "alert" | "verification"
}
```

Event:

```ts
interface AgentEvent {
  type: "message" | "plan" | "device_state" | "command_output" | "config_diff" | "approval" | "task_progress" | "alert" | "verification"
  sessionId: string
  message?: string
  payload?: Record<string, unknown>
  state?: "thinking" | "planning" | "waiting_approval" | "running" | "verifying" | "completed" | "failed"
}
```

## Rules

- Keep the frontend on typed service calls.
- Do not hardcode backend URLs in components.
- Document missing endpoints as explicit backend gaps.
- Update docs and logs whenever the contract changes.

## Agent state contract

The agent page should treat the following states as first-class backend events, not only local UI labels:

- `thinking`
- `planning`
- `waiting_approval`
- `running`
- `verifying`
- `completed`
- `failed`

Use the state field to drive badges, progress bars, execution timelines, and approval prompts in the frontend.
