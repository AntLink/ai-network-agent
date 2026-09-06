param([string]$Port = "18000")
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$SourceApp = Join-Path $RepoRoot "openhands\source\openhands-app"
$keyFile = Join-Path $Root ".session-api-key"
$env:SESSION_API_KEY = (Get-Content -Raw $keyFile).Trim()
$env:OPENHANDS_SUPPRESS_BANNER = "1"
Set-Location $SourceApp
& (Join-Path $RepoRoot "env\Scripts\python.exe") -m openhands.agent_server --host 127.0.0.1 --port $Port
