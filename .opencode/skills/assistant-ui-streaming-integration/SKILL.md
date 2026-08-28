---
name: assistant-ui-streaming-integration
description: Wire assistant-ui to streaming chat backends using SSE or WebSocket, including token streaming, partial updates, abort, retry, reconnect, and live task or command progress for the AI Network Agent dashboard.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Streaming Integration

Use this skill when the task is about live tokens, stream events, or incremental response rendering.

## Focus

- SSE or WebSocket transport.
- Streaming assistant text.
- Partial updates for plans and progress.
- Abort/cancel support.
- Retry and reconnect behavior.
- Live status for long-running operations.

## Expectations

- UI shows running/typing state.
- Partial assistant output renders without losing prior content.
- Stream errors degrade gracefully to a visible error state.
- Reconnect should resume the active session when possible.
- Streaming should support both chat and operational events.

## Event types

- `message`
- `task_progress`
- `command_output`
- `approval`
- `verification`
- `alert`

## Safety

- Never stream secrets into the UI.
- Never expose raw SSH credentials in client state.
- Prefer backend-controlled streaming over direct device access.

