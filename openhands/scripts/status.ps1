$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root ".pids.json"
if (-not (Test-Path $PidFile)) { Write-Host "OpenHands local runtime: stopped"; exit 0 }
$pids = Get-Content $PidFile | ConvertFrom-Json
foreach ($service in @(
  @{ name = "agent"; port = $pids.agentPort },
  @{ name = "automation"; port = $pids.automationPort },
  @{ name = "static"; port = $pids.frontendPort },
  @{ name = "ingress"; port = $pids.canvasPort },
  @{ name = "mcp-bridge"; port = $pids.mcpPort }
)) {
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $client.Connect("127.0.0.1", [int]$service.port)
    $state = "running"
  } catch {
    $state = "stopped"
  } finally {
    $client.Dispose()
  }
  Write-Host ("{0,-12} PORT {1,-7} {2}" -f $service.name, $service.port, $state)
}
