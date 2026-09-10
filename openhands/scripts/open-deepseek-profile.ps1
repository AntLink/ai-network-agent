$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Profile = Join-Path $Root "runtime\deepseek-browser-profile"
$Chrome = @(
  (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
  (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
  (Join-Path $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Chrome) { throw "Google Chrome tidak ditemukan." }
New-Item -ItemType Directory -Force $Profile | Out-Null
Start-Process -FilePath $Chrome -ArgumentList @("--user-data-dir=$Profile", "--profile-directory=Default", "https://chat.deepseek.com/")
Write-Host "Login DeepSeek pada window ini. Profile: $Profile"
