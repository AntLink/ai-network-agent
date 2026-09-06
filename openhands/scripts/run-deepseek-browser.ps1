$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$App = Join-Path $RepoRoot "openhands\source\openhands-app"
$env:DEEPSEEK_BROWSER_API_KEY = if ($env:DEEPSEEK_BROWSER_API_KEY) { $env:DEEPSEEK_BROWSER_API_KEY } else { (Get-Content -Raw (Join-Path $Root ".session-api-key")).Trim() }
$env:DEEPSEEK_BROWSER_PROFILE_DIR = if ($env:DEEPSEEK_BROWSER_PROFILE_DIR) { $env:DEEPSEEK_BROWSER_PROFILE_DIR } else { Join-Path $RepoRoot "runtime\deepseek-browser-profile" }
$env:DEEPSEEK_BROWSER_HEADLESS = if ($env:DEEPSEEK_BROWSER_HEADLESS) { $env:DEEPSEEK_BROWSER_HEADLESS } else { "true" }
$env:DEEPSEEK_BROWSER_TIMEOUT_MS = if ($env:DEEPSEEK_BROWSER_TIMEOUT_MS) { $env:DEEPSEEK_BROWSER_TIMEOUT_MS } else { "300000" }
Set-Location $App
& node (Join-Path $Root "deepseek-browser-bridge\server.mjs")
