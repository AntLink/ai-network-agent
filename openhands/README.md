# OpenHands Source Runtime

OpenHands source and runtime controls for AI Network Agent.

## Run

From the repository root:

```powershell
npm run openhands:start
npm run openhands:status
npm run openhands:stop
```

The runtime uses the project environment `env` and the editable source checkouts:

```text
openhands/source/openhands-app
openhands/source/software-agent-sdk
```

The editable source checkouts are local working repositories and are intentionally
not vendored into this repository commit. Clone or provision them separately when
setting up the OpenHands runtime; runtime databases, session keys, logs, backups,
build output, and dependency directories are also excluded from version control.

The UI is available at <http://localhost:8021/> and the Network Automation API
remains available at <http://127.0.0.1:8000/>. MCP Bridge SSE is available at
<http://127.0.0.1:8911/sse>.

## DeepSeek Browser Profile (Experimental)

This optional bridge uses a dedicated Chrome profile and does not read or copy
the main Chrome profile cookies. Create and log in to the profile once:

```powershell
powershell -ExecutionPolicy Bypass -File openhands/scripts/open-deepseek-profile.ps1
```

Close that dedicated Chrome window, then start the local compatibility bridge:

```powershell
powershell -ExecutionPolicy Bypass -File openhands/scripts/run-deepseek-browser.ps1
```

Configure an OpenHands LLM profile with base URL `http://127.0.0.1:19000/v1`,
model `openai/deepseek-browser`, and the same local session key as the bearer key.
This provider is experimental and remains disabled unless started explicitly.
Generated images found in the browser page are captured as local PNG assets
under `runtime/chatgpt-browser-generated/` or
`runtime/deepseek-browser-generated/` and returned as local asset URLs.
