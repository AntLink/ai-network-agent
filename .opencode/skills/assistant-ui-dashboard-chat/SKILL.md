---
name: assistant-ui-dashboard-chat
description: Integrate assistant-ui into the AI Network Agent dashboard as a polished ChatGPT-style web chat with thread history, resumable sessions, backend routing, network-safe response cards, and readable message rendering.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Dashboard Chat

Use this skill when implementing, reviewing, or improving the `/agent` dashboard chat experience with `assistant-ui`.

The target is a production-quality AI Network Agent chat that feels close to ChatGPT web: clean thread list, persistent chat history, resumable sessions, streaming-friendly responses, polished message cards, markdown/code rendering, attachments, and network-automation safety affordances.

## Current Project Context

This project already uses:

- React + Vite + TypeScript
- Tailwind CSS + shadcn/Base UI
- `@assistant-ui/react`
- `@assistant-ui/ai-sdk`
- `/agent` route in `src/routes/Router.tsx`
- `src/views/agent/index.tsx`
- `src/components/assistant-ui/index.tsx`
- `src/components/assistant-ui/thread.tsx`
- `src/components/assistant-ui/chat-adapter.ts`

Do not replace the dashboard design system or create an unrelated chat application. Improve the existing dashboard integration.

## Official Assistant-UI Baseline

Follow assistant-ui's official runtime shape:

```tsx
import { AssistantRuntimeProvider } from "@assistant-ui/react"
import { useChatRuntime, AssistantChatTransport } from "@assistant-ui/ai-sdk"
```

Preferred provider pattern:

```tsx
const runtime = useChatRuntime({
  transport: new AssistantChatTransport({
    api: "/api/chat",
  }),
})

return (
  <AssistantRuntimeProvider runtime={runtime}>
    <ThreadList />
    <Thread />
  </AssistantRuntimeProvider>
)
```

If the backend is not AI SDK compatible yet, a custom `ChatModelAdapter` is acceptable as a temporary bridge, but keep the component boundary ready to switch to `AssistantChatTransport`.

Official docs verified:

- `https://www.assistant-ui.com/docs/installation`
- `https://www.assistant-ui.com/docs/api-reference/context-providers/assistant-runtime-provider`
- `https://www.assistant-ui.com/docs/runtimes/ai-sdk/v7`

Before using a new assistant-ui API, check installed package versions and official docs because this library changes quickly.

## Required UX

The `/agent` page must provide:

- ChatGPT-like main chat column.
- Thread/session list sidebar.
- New chat button.
- Rename/delete session actions.
- Continue/resume previous sessions.
- Message history per session.
- Clear visual distinction between user and assistant.
- Streaming/loading state.
- Retry/regenerate action.
- Copy message/code action.
- Markdown rendering.
- Code block rendering with language label and copy button.
- Attachments affordance for files/topology/context.
- Device selector and lab selector.
- Safety mode selector such as read-only, guarded, lab-only.
- Empty state with useful prompt examples.
- Error state with retry and backend status hint.

The UI must look intentional and readable in dark mode. Avoid raw JSON blocks as normal responses.

## Session Persistence

Chat sessions must be first-class data, not only transient component state.

Frontend type shape:

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

interface AgentMessage {
  id: string
  sessionId: string
  role: "user" | "assistant" | "system" | "tool"
  content: string
  createdAt: string
  type?: "message" | "plan" | "device_state" | "command_output" | "config_diff" | "approval" | "task_progress" | "alert" | "verification"
}
```

Preferred backend endpoints:

```text
GET    /api/v1/agent/sessions
POST   /api/v1/agent/sessions
GET    /api/v1/agent/sessions/{session_id}
PATCH  /api/v1/agent/sessions/{session_id}
DELETE /api/v1/agent/sessions/{session_id}
GET    /api/v1/agent/sessions/{session_id}/messages
POST   /api/v1/agent/sessions/{session_id}/messages
GET    /api/v1/agent/sessions/{session_id}/events
```

If backend endpoints are not available yet:

- Use a frontend service layer with MSW/local fallback.
- Keep local persistence scoped and replaceable.
- Do not store credentials or provider API keys.
- Mark fallback clearly in docs/logs.

Session resume requirements:

- Opening `/agent` loads the most recent session.
- Selecting a session restores its messages.
- Sending a message appends to the active session.
- Browser reload does not lose visible history.
- If a run was interrupted, show `Resume` or `Retry`, not a blank screen.

## Backend Contract

The browser must not call LLM providers or SSH devices directly.

Allowed frontend flow:

```text
assistant-ui component
  -> src/api/agent.ts or existing service layer
  -> FastAPI backend
  -> AI provider abstraction / network tools
```

Minimum chat request:

```json
{
  "session_id": "session-id",
  "message": "Check why R1 cannot ping R2",
  "device_ids": ["cisco-iosv-r1"],
  "lab_id": "gns3-lab-id",
  "mode": "guarded"
}
```

Minimum response:

```json
{
  "message_id": "msg-id",
  "session_id": "session-id",
  "content": "Readable assistant answer",
  "cards": []
}
```

Streaming should use SSE or WebSocket:

```text
agent_message
task_progress
command_output
approval
verification
alert
```

## Network Copilot Safety

The agent UI is not a raw command launcher.

Required workflow for change requests:

```text
User Request -> Agent Plan -> Validate -> Dry Run -> Approval -> Backup -> Execute -> Verify -> Audit
```

Do not allow destructive changes from a single chat response.

Risky actions require an approval card showing:

- device/lab target
- generated commands/config
- risk level
- backup status
- validation plan
- Execute/Cancel buttons

LLM output should be structured intent. Backend drivers translate to Cisco IOS, MikroTik RouterOS, Aruba AOS-CX, GNS3, or Containerlab operations.

## Message Rendering

Assistant responses should be easy to scan.

Use dedicated renderers for:

- `message`: normal markdown.
- `plan`: numbered plan with risk badge.
- `device_state`: cards/table for hostname, vendor, IP, SSH, CPU, memory, interfaces.
- `command_output`: terminal-like block with copy, explain, collapse.
- `config_diff`: side-by-side or inline diff with added/removed/changed styling.
- `approval`: decision card with clear buttons.
- `task_progress`: timeline with step status.
- `alert`: severity card.
- `verification`: checklist/table.

Do not show backend JSON directly unless in a collapsible debug section.

## Visual Direction

Target visual feel:

- ChatGPT web-like readability.
- Network operations cockpit details around the chat.
- Calm dark mode.
- Clear status colors, not colorful clutter.
- Rounded message bubbles/cards.
- Subtle sticky composer.
- Thread list with active session highlight.
- Good spacing and typography.
- Tables/cards for technical details.

Suggested layout:

```text
/agent
+--------------------------------------------------------------+
| Header: title, model/status, device/lab selector, safety mode |
+---------------+-------------------------------+--------------+
| Thread list   | Chat thread                   | Context/Risk |
| New chat      | Messages + cards              | Plan/status  |
| Search        | Sticky composer               | Devices      |
+---------------+-------------------------------+--------------+
```

Mobile:

- Thread list becomes drawer/sheet.
- Context panel collapses below chat.
- Composer remains sticky.

## Implementation Order

1. Read current files:
   - `src/views/agent/index.tsx`
   - `src/components/assistant-ui/index.tsx`
   - `src/components/assistant-ui/thread.tsx`
   - `src/components/assistant-ui/chat-adapter.ts`
   - `src/api/network/backend-client.ts`
   - `src/types/network.ts`
2. Add/adjust agent types.
3. Add `src/api/agent.ts` or extend service layer.
4. Implement session list and persistence.
5. Improve Thread UI and message renderers.
6. Wire backend or MSW/local fallback.
7. Add loading/error/empty states.
8. Validate dark/light and responsive behavior.
9. Run:

```bash
npm run lint
npm run build
```

Do not mark complete if either fails.

## Quality Gates

Done only when:

- `/agent` route loads without console errors.
- Existing dashboard layout remains intact.
- Chat history persists across reload.
- User can create, switch, rename, delete, and resume sessions.
- Assistant response is readable and card-based where structured.
- No raw secrets or provider keys in browser storage.
- Risky network changes require approval UI.
- Loading, empty, error, and streaming states exist.
- `npm run lint` passes.
- `npm run build` passes.

## Documentation

After implementation, update:

- `README.md` if setup or runtime changed.
- `docs/FRONTEND_BACKEND_INTEGRATION.md` for endpoint/session contract.
- `logs/SESSION-YYYY-MM-DD-assistant-ui-dashboard-chat.md` with changes and validation.
