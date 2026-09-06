$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$App = Join-Path $RepoRoot "openhands\source\openhands-app"
$env:BROWSER_PROVIDER = "claude"
$env:CLAUDE_BROWSER_API_KEY = if ($env:CLAUDE_BROWSER_API_KEY) { $env:CLAUDE_BROWSER_API_KEY } else { (Get-Content -Raw (Join-Path $Root ".session-api-key")).Trim() }
$env:CLAUDE_BROWSER_PROFILE_DIR = if ($env:CLAUDE_BROWSER_PROFILE_DIR) { $env:CLAUDE_BROWSER_PROFILE_DIR } else { Join-Path $RepoRoot "runtime\claude-browser-profile" }
$env:CLAUDE_BROWSER_HEADLESS = if ($env:CLAUDE_BROWSER_HEADLESS) { $env:CLAUDE_BROWSER_HEADLESS } else { "false" }
$env:CLAUDE_BROWSER_PORT = if ($env:CLAUDE_BROWSER_PORT) { $env:CLAUDE_BROWSER_PORT } else { "19002" }
$env:CLAUDE_BROWSER_TIMEOUT_MS = if ($env:CLAUDE_BROWSER_TIMEOUT_MS) { $env:CLAUDE_BROWSER_TIMEOUT_MS } else { "120000" }
$env:CLAUDE_BROWSER_CLOSE_AFTER_RESPONSE = if ($env:CLAUDE_BROWSER_CLOSE_AFTER_RESPONSE) { $env:CLAUDE_BROWSER_CLOSE_AFTER_RESPONSE } else { "false" }
Set-Location $App
& node (Join-Path $Root "deepseek-browser-bridge\server.mjs")
