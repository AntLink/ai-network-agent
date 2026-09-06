#!powershell
# ============================================================
#  Resume opencode session — DeepSeek Bridge & Code Review
#  Sesi ini  : "Can I use consult_deepseek_browser?"
#  Sesi ID   : ses_fa1833fe9ffe5G7ylRb3cDHo4s
#  Dibuat    : 2026-09-02
#
#  Cara pakai:  .\resume-deepseek-session.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# Working directory proyek
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Pilih mode: default = lanjut sesi asli (resume)
# Argumen -Fork = buat salinan sesi (tidak mengubah si asli)
$fork = $args -contains "-Fork" -or $args -contains "-fork"

$id  = "ses_fa1833fe9ffe5G7ylRb3cDHo4s"
$arg = if ($fork) { "--session $id --fork" } else { "--session $id" }
$msg = if ($fork) { "  Fork session (salinan)  " } else { "  Lanjut session asli    " }

Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "  Resume opencode session...  " -ForegroundColor Cyan
Write-Host $msg -ForegroundColor Yellow
Write-Host "  ID : $id" -ForegroundColor Cyan
Write-Host "  Log: logs\SESSION-2026-09-02-deepseek-bridge-timeout-review.md" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

# Catatan: config opencode.json baru (mcp_timeout 600000) dibaca
# saat startup, jadi pastikan opencode sudah di-TUTUP dulu sebelum
# menjalankan script ini (bukan launch ulang di dalam sesi yang sama).
& opencode @($arg.Split(" "))