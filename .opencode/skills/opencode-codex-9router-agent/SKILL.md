---
name: opencode-codex-9router-agent
description: Build or update OpenCode workflows that use Codex SDK in the backend and 9Router as the model routing layer for agent chat, session resume, streaming, approval, and plan/execute/verify flows.
metadata:
  opencode/autoinvoke: "true"
---

# OpenCode Codex 9Router Agent

Use this skill when working on an OpenCode-based agent workflow that combines:

- Codex SDK as the backend agent engine.
- 9Router as the provider/model router.
- An agent orchestration layer that coordinates chat, session, plan, approval, and execution state.

This skill is intentionally narrow. It complements, but does not replace:

- `openhands-software-agent-sdk-9router-hybrid` for OpenHands software-agent-sdk + 9Router hybrid backend architecture.
- `assistant-ui-session-manager` for session/thread persistence.
- `assistant-ui-backend-contract` for event and API contract design.
- `assistant-ui-dashboard-chat` for the ChatGPT-like `/agent` UI.
- `assistant-ui-streaming-integration` for token/event streaming.
- `ai-network-agent-backend-integration` for wiring real backend endpoints.
- `ai-network-agent-frontend` for broader frontend layout and page work.

## Required architecture

- Keep Codex SDK in the backend.
- Keep provider keys and routing secrets out of the frontend.
- Use 9Router as an OpenAI-compatible routing layer, not as a UI concern.
- Persist conversation/session state so refresh and resume work cleanly.
- For network automation, follow `Plan -> Validate -> Execute -> Verify`.
- Do not duplicate the responsibilities of the existing assistant-ui or backend-integration skills.
- If the request is specifically about OpenHands software-agent-sdk, prefer `openhands-software-agent-sdk-9router-hybrid`.
- If the task is mostly UI polish, page layout, or endpoint wiring, hand off to the corresponding skill instead of expanding this one.

## Agent UI states

The `/agent` page must expose these explicit states:

- `Thinking`
- `Planning`
- `Waiting approval`
- `Running`
- `Verifying`
- `Completed`
- `Failed`

Render these states as chips, timeline steps, or progress cards so the user can see what the agent is doing.

## What the frontend should render

The agent UI should not be a plain chatbot. Prefer dedicated renderers for:

- message
- plan
- device_state
- command_output
- config_diff
- approval
- task_progress
- verification
- error

## Provider routing

Use 9Router aliases or tiers to separate task cost and quality:

- `cheap` for discovery or simple helper calls.
- `coder` for implementation and normal debugging.
- `reasoning` for architecture, hard bugs, or security-sensitive work.

Do not hardcode provider secrets in the client.

## Safety rules

- Approval is required before risky or destructive actions.
- If device or target context is ambiguous, ask for clarification before executing.
- Do not let the browser run SSH, network automation, or provider calls directly.

## Recommended backend shape

- Agent orchestrator
- Provider abstraction
- Thread/session store
- Event stream
- Tool layer for device, lab, config, and verification work

The frontend should only call backend endpoints and render streamed events.
