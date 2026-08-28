@echo off
REM Jalankan MCP bridge dalam mode SSE untuk OpenHands/Agent Canvas.
REM Setelah jalan, daftarkan URL berikut di OpenHands:
REM   Customize > MCP Servers > Add > SSE: http://127.0.0.1:8911/sse
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [setup] Membuat virtual environment...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
set MCP_TRANSPORT=sse
set MCP_HOST=127.0.0.1
set MCP_PORT=8911
".venv\Scripts\python.exe" server.py