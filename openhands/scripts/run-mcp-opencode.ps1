$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$KeyFile = Join-Path $Root "openhands\.session-api-key"
$Python = Join-Path $Root "env\Scripts\python.exe"
$Server = Join-Path $Root "mcp-bridge\server.py"

if (-not (Test-Path $Python)) { throw "Python environment tidak ditemukan: $Python" }
if (-not (Test-Path $KeyFile)) { throw "Session API key tidak ditemukan: $KeyFile" }

$key = (Get-Content -Raw $KeyFile).Trim()
$env:MCP_TRANSPORT = "stdio"
$env:DEEPSEEK_BROWSER_API_KEY = $key
$env:CHATGPT_BROWSER_API_KEY = $key
$env:CLAUDE_BROWSER_API_KEY = $key
$env:DEEPSEEK_BROWSER_URL = "http://127.0.0.1:19000/v1"
$env:CHATGPT_BROWSER_URL = "http://127.0.0.1:19001/v1"
$env:CLAUDE_BROWSER_URL = "http://127.0.0.1:19002/v1"

& $Python $Server
exit $LASTEXITCODE
