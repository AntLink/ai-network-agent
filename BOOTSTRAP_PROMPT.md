# OpenCode V2 Bootstrap Prompt

1. Copy the `skills/`, `agents/`, `tools/`, and `opencode.json` to your OpenCode project.
2. Open OpenCode and invoke the `network-planner` agent to test read-only operations.
3. Invoke `network-operator` to test change workflows (requires approval).

## Recommended Flow
- User asks a question → `network-planner` or `network-troubleshooter` is triggered.
- User requests a change → `network-planner` drafts plan → `network-operator` requests approval → applies → verifies.

## Extending
To add a new vendor:
1. Create `skills/<vendor>/SKILL.md` with command mappings.
2. Add identification logic to `device_identify` tool.
3. Ensure `config_plan` supports the vendor syntax.

## Testing
Test each tool and agent in isolation before production.
