$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$App = Join-Path $RepoRoot "openhands\source\openhands-app"
$env:BROWSER_PROVIDER = "chatgpt"
$env:CHATGPT_BROWSER_API_KEY = if ($env:CHATGPT_BROWSER_API_KEY) { $env:CHATGPT_BROWSER_API_KEY } else { (Get-Content -Raw (Join-Path $Root ".session-api-key")).Trim() }
$env:CHATGPT_BROWSER_PROFILE_DIR = if ($env:CHATGPT_BROWSER_PROFILE_DIR) { $env:CHATGPT_BROWSER_PROFILE_DIR } else { Join-Path $RepoRoot "runtime\chatgpt-browser-profile" }
$env:CHATGPT_BROWSER_HEADLESS = if ($env:CHATGPT_BROWSER_HEADLESS) { $env:CHATGPT_BROWSER_HEADLESS } else { "false" }
$env:CHATGPT_BROWSER_PORT = if ($env:CHATGPT_BROWSER_PORT) { $env:CHATGPT_BROWSER_PORT } else { "19001" }
$env:CHATGPT_BROWSER_TIMEOUT_MS = if ($env:CHATGPT_BROWSER_TIMEOUT_MS) { $env:CHATGPT_BROWSER_TIMEOUT_MS } else { "300000" }
$env:CHATGPT_BROWSER_CLOSE_AFTER_RESPONSE = if ($env:CHATGPT_BROWSER_CLOSE_AFTER_RESPONSE) { $env:CHATGPT_BROWSER_CLOSE_AFTER_RESPONSE } else { "true" }
$env:CHATGPT_BROWSER_IMAGE_WAIT_MS = if ($env:CHATGPT_BROWSER_IMAGE_WAIT_MS) { $env:CHATGPT_BROWSER_IMAGE_WAIT_MS } else { "50000" }
$env:CHATGPT_BROWSER_ATTACHMENT_UPLOAD_WAIT_MS = if ($env:CHATGPT_BROWSER_ATTACHMENT_UPLOAD_WAIT_MS) { $env:CHATGPT_BROWSER_ATTACHMENT_UPLOAD_WAIT_MS } else { "25000" }
Set-Location $App
& node (Join-Path $Root "deepseek-browser-bridge\server.mjs")
