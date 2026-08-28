# OpenCode Codex 9Router Agent Workflow

Use this reference when implementing or updating the backend-to-frontend agent flow.

## UI states

The `/agent` page should visibly expose:

- `Thinking`
- `Planning`
- `Waiting approval`
- `Running`
- `Verifying`
- `Completed`
- `Failed`

## Event types

Prefer these event categories in streaming:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `verification`
- `error`
- `done`

## Session persistence

Persist enough data to resume safely:

- session id
- selected provider/model
- user messages
- assistant messages
- approval state
- task progress
- verification result

## Provider routing

Route by task quality and cost:

- `cheap` for discovery
- `coder` for implementation
- `reasoning` for planning and hard failures

## Clarification rule

If the target device or action is ambiguous, clarify before executing a risky change.
