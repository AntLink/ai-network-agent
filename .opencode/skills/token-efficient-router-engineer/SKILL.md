---
name: token-efficient-router-engineer
description: Use 9Router and compact engineering workflows to reduce token/cost usage in OpenCode, with STRICT/BALANCED/DEEP modes, model escalation rules, context budgets, and network automation safety boundaries.
metadata:
  opencode/autoinvoke: "true"
---

# Token Efficient Router Engineer

Use this skill when the user wants OpenCode work to be token-efficient, cost-aware, or routed through 9Router model tiers.

This skill complements `nine-router-lab-setup`. That skill handles 9-router lab configuration. This skill handles model routing, context discipline, and escalation rules.

## Core idea

Route work by task difficulty:

```text
scout      -> cheap model
coder      -> coding model
reviewer   -> coder/reasoning depending on risk
architect  -> reasoning model
```

Keep the model gateway OpenAI-compatible:

```text
OpenCode -> http://127.0.0.1:20128/v1 -> 9Router combos/providers
```

Do not hardcode provider keys in project files. Use 9Router/provider secret storage or environment variables.

## Current OpenCode mapping

The Windows OpenCode global config is expected to use:

```text
model: 9router/opencode-coder
small_model: 9router/opencode-cheap
```

Recommended agent mapping:

```text
explore/explorer -> 9router/opencode-cheap
general/build    -> 9router/opencode-coder
plan/architect   -> 9router/opencode-reasoning
```

Project network agents should use `9router/opencode-reasoning` because network planning, troubleshooting, audit, and approved operations are safety-sensitive.

## Claude Code CLI mapping

Claude Code should route through 9Router with:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:20128/v1
```

Use `ANTHROPIC_AUTH_TOKEN` for the 9Router bearer token. Do not print it.

Recommended Claude Code model mapping:

```text
Claude Sonnet alias -> opencode-coder
Claude Opus alias   -> opencode-reasoning
Claude Haiku alias  -> opencode-cheap
```

Prefer `modelOverrides` so Claude Code sees recognized Anthropic model IDs while 9Router receives combo names:

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "modelOverrides": {
    "claude-sonnet-4-5-20250929": "opencode-coder",
    "claude-opus-4-5-20251101": "opencode-reasoning",
    "claude-haiku-4-5-20251001": "opencode-cheap"
  }
}
```

This avoids `unrecognized_model` warnings while keeping routing through 9Router.

## OpenCode CLI troubleshooting

If OpenCode shows:

```text
Failed to send prompt
Unexpected server error. Check server logs for details.
```

Run:

```powershell
& "C:\Users\mohfa\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe" run "Reply only: ok" --print-logs --log-level INFO
```

Known project-specific failure:

```text
Cannot find module '../../src/api-client.js' from '.opencode/tools/policy_check.ts'
```

Fix by keeping `src/api-client.js` compatibility shim because `.opencode/tools/*` imports it.

Known Windows CLI path issue:

```text
where opencode
```

may resolve first to:

```text
C:\Windows\System32\opencode
```

If that file is 0 bytes, it shadows the real npm OpenCode command and causes `Access is denied`. Use the real wrapper:

```powershell
& "C:\Users\mohfa\AppData\Roaming\npm\opencode.cmd"
```

or the binary:

```powershell
& "C:\Users\mohfa\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe"
```

Removing the System32 stub requires elevated Windows/admin permission.

## Preferred local 9Router combos

Use these combo names when available:

- `opencode-cheap`
- `opencode-coder`
- `opencode-reasoning`

Recommended model order for this project:

```text
opencode-cheap
1. oc/laguna-s-2.1-free
2. cf/@cf/zai-org/glm-4.7-flash
3. mistral/codestral-latest

opencode-coder
1. ocg/deepseek-v4-flash
2. mistral/codestral-latest
3. cx/gpt-5.4-mini
4. nvidia/nvidia/nemotron-3-ultra-550b-a55b

opencode-reasoning
1. cx/gpt-5.4-mini
2. nvidia/nvidia/nemotron-3-ultra-550b-a55b
3. cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b
4. cf/@cf/moonshotai/kimi-k2.5
5. ocg/deepseek-v4-flash
```

`ocg/deepseek-v4-flash` is the default coder workhorse. `nvidia/nvidia/nemotron-3-ultra-550b-a55b` is for escalation, not default trivial work.
`cx/gpt-5.4-mini` is a paid Codex fallback for coder/reasoning work, not for cheap mode.
Do not put unavailable/EOL models in the front of default combos.

## Modes

### STRICT

Use when the user says `STRICT`, `hemat token`, `murah dulu`, or similar.

- Start with cheap/scout behavior.
- Read only the files needed for the next decision.
- Avoid full repository dumps and long raw logs.
- Use reasoning model only when:
  - bug remains after 2 concrete hypotheses,
  - change crosses more than 5 files,
  - security/architecture/data-loss risk is present,
  - user explicitly asks for deep review.

### BALANCED

Default mode for normal project work.

- Discovery uses compact read/search.
- Implementation uses coder behavior.
- Reasoning model is allowed for planning complex changes, but not for routine file edits.
- Summaries should include decision, changed files, validation, and next step only.

### DEEP

Use when user asks for deep review, architecture, security, or complex refactor.

- Reasoning model is allowed.
- Still cap tool output and avoid raw dumps.
- Use structured findings, plans, and diffs.
- Do not perform destructive work without confirmation.

## Context budgets

Default budgets unless the user asks otherwise:

- File discovery: max 20 filenames per pass.
- File reads: max 5 files before deciding next step.
- Logs/build output: first relevant error plus 40 lines around it.
- Git diff: changed files list first, then targeted diff only.
- Terminal/device output: summarize success; show raw only for failed checks.
- Documentation updates: append concise section instead of rewriting entire docs.

For large output, reduce before sending to model:

- filter by exact error string
- select first/last relevant lines
- group by file/device/status
- summarize duplicate failures

## Tool-output discipline

Prefer:

- `rg --files` over recursive directory dumps
- `rg -n "pattern"` over opening many files
- targeted `Select-Object -First/-Last`
- backend API summaries over full raw CLI
- tables for multi-device status

Avoid:

- reading `node_modules`, generated clients, pycache, build artifacts
- pasting full configs for all devices
- repeating identical explanations
- running broad commands when a targeted command answers the question

## Escalation rules

Escalate from cheap to coder when:

- a code edit is needed,
- TypeScript/Python errors need interpretation,
- behavior spans frontend and backend,
- parser/service logic is failing.

Escalate from coder to reasoning when:

- multiple plausible root causes remain after targeted tests,
- architecture boundary is unclear,
- network safety could be affected,
- refactor touches many modules,
- destructive operation or rollback logic is involved,
- user requests full codebase review/security review.

Do not escalate just because output is long. First reduce the output.

## Network automation safety

Even in token-saving mode:

- never put SSH credentials in frontend code
- never store provider keys in repo
- never let LLM execute SSH directly
- route network changes through backend tools
- use `Plan -> Validate -> Execute -> Verify`
- require approval for config changes
- backup before deploy
- verify after deploy

## Output style

For normal updates:

```text
Mode: STRICT
Model route: cheap -> coder if needed
Scope: terminal autocomplete parser
Next: inspect backend parser test
```

For final:

```text
Result: completed
Files: 3 changed
Validation: lint/build passed
Cost control: no raw dumps; targeted reads only
Next: optional backend integration
```

Keep Indonesian responses concise when the user writes in Indonesian.

## 9Router setup check

Read-only checks:

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -eq 20128 }
Invoke-RestMethod http://127.0.0.1:20128/v1/models
```

Safe combo names for OpenCode:

```text
opencode-cheap
opencode-coder
opencode-reasoning
```

If changing 9Router SQLite config directly, backup `data.sqlite` first and never print secret-bearing fields such as `apiKeys.key`, provider `data`, or token values.

## Local setup helper

This skill includes an idempotent helper:

```text
.opencode/skills/token-efficient-router-engineer/scripts/setup_9router_opencode_combos.py
```

It creates or updates only these 9Router combo rows:

- `opencode-cheap`
- `opencode-coder`
- `opencode-reasoning`

The helper backs up `data.sqlite` first and does not read or print provider secrets. Because it writes to the user's 9Router AppData database, get explicit approval before running it.
