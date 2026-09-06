param([ValidateSet("deepseek", "chatgpt", "claude")][string]$Provider)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PSScriptRoot ("run-{0}-browser.ps1" -f $Provider)
$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null

$outLog = Join-Path $Logs ("{0}-browser.out.log" -f $Provider)
$errLog = Join-Path $Logs ("{0}-browser.err.log" -f $Provider)
$process = Start-Process powershell.exe -WindowStyle Hidden -WorkingDirectory $Root -ArgumentList @(
  "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $Runner
) -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru

Write-Host ("{0} browser bridge started in background (PID {1}). Logs: {2}" -f $Provider, $process.Id, $outLog)
