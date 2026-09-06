$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$CanvasSource = Join-Path $RepoRoot "openhands\source\openhands-app"
$CanvasPackage = if (Test-Path (Join-Path $CanvasSource "scripts\ingress.mjs")) { $CanvasSource } else { Join-Path $Root "agent-canvas\node_modules\@openhands\agent-canvas" }
$ProjectPython = Join-Path $RepoRoot "env\Scripts\python.exe"
$AutomationPython = $ProjectPython
$McpBridge = Join-Path $RepoRoot "mcp-bridge\server.py"
$PidFile = Join-Path $Root ".pids.json"
$Logs = Join-Path $Root "logs"
$SessionKeyFile = Join-Path $Root ".session-api-key"
$EnvFile = Join-Path $Root ".env"
$AgentRunner = Join-Path $PSScriptRoot "run-agent-server.ps1"
$AutomationRunner = Join-Path $PSScriptRoot "run-automation.ps1"

if (-not (Test-Path $CanvasPackage)) { throw "Agent Canvas source belum tersedia: $CanvasSource" }
if (-not (Test-Path $ProjectPython)) { throw "Python env project tidak ditemukan: $ProjectPython" }
if (-not (Test-Path $McpBridge)) { throw "MCP Bridge tidak ditemukan: $McpBridge" }
New-Item -ItemType Directory -Force $Logs | Out-Null

if (Test-Path $EnvFile) {
  Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') { Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim() }
  }
}

$config = @{
  canvas = if ($env:CANVAS_PORT) { $env:CANVAS_PORT } else { "8021" }
  frontend = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { "3001" }
  agent = if ($env:AGENT_SERVER_PORT) { $env:AGENT_SERVER_PORT } else { "18000" }
  automation = if ($env:AUTOMATION_PORT) { $env:AUTOMATION_PORT } else { "18001" }
  mcp = if ($env:MCP_PORT) { $env:MCP_PORT } else { "8911" }
}

if ($env:LOCAL_BACKEND_API_KEY) {
  $sessionKey = $env:LOCAL_BACKEND_API_KEY
} elseif (Test-Path $SessionKeyFile) {
  $sessionKey = (Get-Content -Raw $SessionKeyFile).Trim()
} else {
  $sessionKey = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))
  Set-Content -Path $SessionKeyFile -Value $sessionKey -NoNewline
}
$automationDbPath = (Join-Path $Root "automation.db").Replace("\", "/")
$env:SESSION_API_KEY = $sessionKey
$env:AUTOMATION_AGENT_SERVER_URL = "http://127.0.0.1:$($config.agent)"
$env:AUTOMATION_AGENT_SERVER_API_KEY = $sessionKey
$env:AUTOMATION_LOCAL_API_KEY = $sessionKey
$env:AUTOMATION_DB_URL = "sqlite+aiosqlite:///$automationDbPath"
$env:DEEPSEEK_BROWSER_API_KEY = $sessionKey
$env:CHATGPT_BROWSER_API_KEY = $sessionKey

$buildDir = Join-Path $CanvasPackage "build"
if (-not (Test-Path $buildDir)) { throw "Agent Canvas frontend belum di-build: $buildDir" }

$agent = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $Root -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $AgentRunner, "-Port", $config.agent) -RedirectStandardOutput (Join-Path $Logs "agent-server.out.log") -RedirectStandardError (Join-Path $Logs "agent-server.err.log") -PassThru
$automation = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $Root -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $AutomationRunner, "-Port", $config.automation) -RedirectStandardOutput (Join-Path $Logs "automation.out.log") -RedirectStandardError (Join-Path $Logs "automation.err.log") -PassThru
$env:MCP_TRANSPORT = "sse"
$env:MCP_HOST = "127.0.0.1"
$env:MCP_PORT = [string]$config.mcp
$mcp = Start-Process -FilePath $ProjectPython -WindowStyle Hidden -WorkingDirectory (Join-Path $RepoRoot "mcp-bridge") -ArgumentList @($McpBridge) -RedirectStandardOutput (Join-Path $Logs "mcp-bridge.out.log") -RedirectStandardError (Join-Path $Logs "mcp-bridge.err.log") -PassThru
Remove-Item Env:MCP_TRANSPORT,Env:MCP_HOST,Env:MCP_PORT,Env:SESSION_API_KEY,Env:AUTOMATION_AGENT_SERVER_URL,Env:AUTOMATION_AGENT_SERVER_API_KEY,Env:AUTOMATION_LOCAL_API_KEY,Env:AUTOMATION_DB_URL,Env:DEEPSEEK_BROWSER_API_KEY,Env:CHATGPT_BROWSER_API_KEY -ErrorAction SilentlyContinue

$staticScript = Join-Path $CanvasPackage "scripts\static-server.mjs"
$ingressScript = Join-Path $CanvasPackage "scripts\ingress.mjs"
$static = Start-Process -FilePath "node.exe" -WindowStyle Hidden -WorkingDirectory $CanvasPackage -ArgumentList @($staticScript, "--dir", $buildDir, "--port", $config.frontend, "--session-api-key", $sessionKey) -RedirectStandardOutput (Join-Path $Logs "static.out.log") -RedirectStandardError (Join-Path $Logs "static.err.log") -PassThru
$ingress = Start-Process -FilePath "node.exe" -WindowStyle Hidden -WorkingDirectory $CanvasPackage -ArgumentList @($ingressScript, "--port", $config.canvas, "--route", "/api/automation=http://127.0.0.1:$($config.automation)", "--route", "/api=http://127.0.0.1:$($config.agent)", "--route", "/sockets=http://127.0.0.1:$($config.agent)", "--route", "/server_info=http://127.0.0.1:$($config.agent)", "--route", "/health=http://127.0.0.1:$($config.agent)", "--route", "/ready=http://127.0.0.1:$($config.agent)", "--route", "/alive=http://127.0.0.1:$($config.agent)", "--route", "/docs=http://127.0.0.1:$($config.agent)", "--route", "/redoc=http://127.0.0.1:$($config.agent)", "--route", "/openapi.json=http://127.0.0.1:$($config.agent)", "--default", "http://127.0.0.1:$($config.frontend)") -RedirectStandardOutput (Join-Path $Logs "ingress.out.log") -RedirectStandardError (Join-Path $Logs "ingress.err.log") -PassThru

@{
  agent = $agent.Id
  automation = $automation.Id
  static = $static.Id
  ingress = $ingress.Id
  mcp = $mcp.Id
  agentPort = [int]$config.agent
  automationPort = [int]$config.automation
  frontendPort = [int]$config.frontend
  canvasPort = [int]$config.canvas
  mcpPort = [int]$config.mcp
} | ConvertTo-Json | Set-Content $PidFile
Write-Host "OpenHands local runtime started: http://localhost:$($config.canvas)/"
