param([string]$Port = "18001")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$SourceApp = Join-Path $RepoRoot "openhands\source\openhands-app"
$keyFile = Join-Path $Root ".session-api-key"
$key = (Get-Content -Raw $keyFile).Trim()
$dbPath = (Join-Path $Root "automation.db").Replace("\", "/")
$env:AUTOMATION_AGENT_SERVER_URL = "http://127.0.0.1:18000"
$env:AUTOMATION_AGENT_SERVER_API_KEY = $key
$env:AUTOMATION_LOCAL_API_KEY = $key
$env:AUTOMATION_DB_URL = "sqlite+aiosqlite:///$dbPath"
$env:AUTOMATION_SERVER_PORT = $Port
$env:OPENHANDS_SUPPRESS_BANNER = "1"
Set-Location $SourceApp
& (Join-Path $RepoRoot "env\Scripts\python.exe") -m uvicorn openhands.automation.app:app --host 127.0.0.1 --port $Port
