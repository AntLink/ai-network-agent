---
name: assistant-ui-session-manager
description: Manage assistant-ui chat sessions for the AI Network Agent dashboard, including thread lists, session resume, create/rename/delete flows, persisted history, and session-scoped message loading.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Session Manager

Use this skill when the task is about chat sessions, thread history, restoring previous conversations, or keeping `/agent` session state persistent across reloads.

## Focus

- Thread/session list UX.
- New chat, rename, delete, archive.
- Resume last session on page load.
- Persisted message history per session.
- Session metadata such as title, device ids, lab id, status, timestamps.

## Rules

- Do not store secrets in browser storage.
- Do not treat chat history as ephemeral local state only.
- Keep the session model backend-first and replaceable.
- If backend session endpoints are missing, use a service layer fallback and document the gap.

## Expected backend shape

Prefer endpoints like:

```text
GET    /api/v1/agent/sessions
POST   /api/v1/agent/sessions
GET    /api/v1/agent/sessions/{session_id}
PATCH  /api/v1/agent/sessions/{session_id}
DELETE /api/v1/agent/sessions/{session_id}
GET    /api/v1/agent/sessions/{session_id}/messages
POST   /api/v1/agent/sessions/{session_id}/messages
```

## UX requirements

- Active session highlight.
- Session search/filter.
- Empty state with sample prompts.
- Session restore after reload.
- Clear loading/error state.
- Session actions reachable on desktop and mobile.

