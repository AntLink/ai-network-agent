# Session Log: Streaming & AI Provider Abstraction

Tanggal: 2026-08-25

## Fokus

Menambahkan WebSocket/SSE streaming dan AI provider abstraction.

## Perubahan

### WebSocket Streaming (Terminal)

- Terminal page sekarang mendukung WebSocket streaming untuk output real-time
- `connectWebSocket()` function menghubungkan ke `WS /api/v1/terminal/sessions/{session_id}/stream`
- WebSocket status indicator ("stream active" / "stream off") ditambahkan ke UI
- Auto-connect WebSocket setelah session SSH dibuat
- Auto-disconnect WebSocket saat session ditutup atau component unmount

### SSE Streaming (Agent & Tasks)

- Backend SSE endpoints ditambahkan:
  - `GET /api/v1/agent/events/stream` - streaming agent events
  - `GET /api/v1/tasks/stream` - streaming task updates
- Frontend SSE client utility dibuat di `src/api/network/sse-client.ts`
  - `connectAgentSSE()` - koneksi SSE untuk agent events
  - `connectTaskSSE()` - koneksi SSE untuk task updates
- Agent page menggunakan SSE untuk menerima real-time messages
- SSE connection status indicator ditambahkan ke Agent UI

### AI Provider Abstraction

- Modul `backend/app/agent/providers.py` dibuat dengan:
  - `AIProvider` base class (abstract)
  - `OpenAIProvider` - OpenAI API (GPT-4, GPT-5)
  - `AnthropicProvider` - Anthropic Claude API
  - `OllamaProvider` - Ollama local LLM
  - `get_provider()` factory function
- Provider selection via environment variable `AI_PROVIDER` atau parameter request
- Support untuk chat dan streaming response
- Fallback ke provider default jika provider tidak tersedia

### Backend Updates

- Agent endpoint `/api/v1/agent/chat` sekarang menggunakan AI provider
- Task endpoint menambahkan SSE streaming support

## File Yang Diubah

Backend:
- `backend/app/agent/__init__.py` (baru)
- `backend/app/agent/providers.py` (baru) - AI provider abstraction
- `backend/app/api/v1/endpoints/agent.py` - tambah provider integration dan SSE
- `backend/app/api/v1/endpoints/tasks.py` - tambah SSE streaming

Frontend:
- `src/api/network/sse-client.ts` (baru) - SSE client utility
- `src/api/network/index.ts` - tambah `getApiBaseUrl` export
- `src/views/terminal/index.tsx` - tambah WebSocket streaming
- `src/views/agent/index.tsx` - tambah SSE connection

## Validasi

- `npm run build` sukses
- `.\env\Scripts\python.exe -m compileall backend\app` sukses (3 packages)
- `.\env\Scripts\python.exe -m pytest backend\tests\ -v` sukses, 6 test passed

## Environment Variables Untuk AI Provider

```bash
# Provider selection
AI_PROVIDER=openai  # or anthropic, ollama

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Status Akhir

- Semua halaman frontend terhubung ke backend
- WebSocket streaming untuk terminal real-time
- SSE streaming untuk agent dan task updates
- AI provider abstraction mendukung OpenAI, Anthropic, dan Ollama
- Semua validasi passing
