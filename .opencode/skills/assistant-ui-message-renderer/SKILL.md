---
name: assistant-ui-message-renderer
description: Render assistant-ui responses as polished operational cards and readable markdown/code blocks for the AI Network Agent dashboard, including plans, diffs, device state, command output, approvals, progress, alerts, and verification.
metadata:
  opencode/autoinvoke: "true"
---

# Assistant UI Message Renderer

Use this skill when the task is about how assistant responses should look, not how the session is stored.

## Message types

Render structured assistant output as dedicated UI blocks:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `alert`
- `verification`

## Rendering rules

- Use markdown for normal narrative answers.
- Use tables or cards for structured device or lab data.
- Use diff styling for config changes.
- Use timeline/checklist UI for progress and verification.
- Use code blocks with copy controls for CLI snippets.
- Do not show raw backend JSON as the main experience.

## Visual rules

- Clear typography.
- Strong spacing.
- Distinct user vs assistant styling.
- Dark mode first.
- Readability over decorative noise.

## Safety

- Approval and risk cards must be obvious.
- Destructive actions should not look like normal chat text.

