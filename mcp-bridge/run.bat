@echo off
REM Jalankan MCP bridge. Membuat venv .venv & install deps otomatis saat pertama kali.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [setup] Membuat virtual environment...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
".venv\Scripts\python.exe" server.py %*