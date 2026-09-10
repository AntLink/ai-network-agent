$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root ".pids.json"
if (Test-Path $PidFile) {
  $pids = Get-Content $PidFile | ConvertFrom-Json
  foreach ($portName in @("canvasPort", "frontendPort", "automationPort", "agentPort", "mcpPort")) {
    $port = [int]$pids.$portName
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique |
      ForEach-Object { Stop-Process -Id ([int]$_) -Force -ErrorAction SilentlyContinue }
  }
  Remove-Item $PidFile -Force
}
Write-Host "OpenHands local runtime stopped."
