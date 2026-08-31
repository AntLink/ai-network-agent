# Session 2026-08-31 - Web Search Tavily via 9Router (true provider + multi-key failover)

## Tujuan

Mengaktifkan web search **sungguhan** (`/v1/search`) untuk agent AI Network Agent
melalui 9Router, menggantikan fallback model `cx/*` (search:true) yang selama ini
menjadi satu-satunya jalur karena tidak ada provider web-search yang terhubung.

## Masalah yang ditemukan

1. **9Router tidak punya provider web-search terhubung.**
   - Semua koneksi di `providerConnections` adalah LLM/chat (gemini, github,
     openai, mistral, codex, dll). Tidak ada Tavily/Exa/Brave/Serper.
   - Konsekuensi: `GET /v1/models/web` kosong, `POST /v1/search` balas
     `Unknown provider`. Backend jatuh ke fallback `_run_web_llm_answer()`
     (model `cx/gpt-5.6-sol`, capability search:true).

2. **Model `oc/big-pickle` TIDAK search-capable.**
   - Terdaftar di DB (combo `9router`, `GPT-GEMINI`, `opencode-coder`) dengan
     definisi murni `{type:"llm"}`, tanpa flag search/web.
   - Tes langsung: HTTP 200 tapi **halusinasi** — nyebut "Rabu 26 Agu 2026"
     (hari ini Senin 31 Agu 2026) & URL Space.com ternyata **404** (berasal dari
     training data, bukan pencarian live). → TIDAK layak jadi ganti `cx/gpt-5.6-sol`.

3. **Identifier model `/v1/search` tidak `search-combo` di instalasi ini.**
   - Tabel `combos` tidak punya baris `search-combo`, jadi `model:"search-combo"`
     → `Unknown provider`.
   - Identifier yang benar: **`tavily`** (bukan `tavily/search`).

## Perbaikan

- **9Router (dashboard http://127.0.0.1:20128):** tambah provider web-search
  **Tavily**, lalu tambah koneksi kedua untuk failover (total 2 akun Tavily):
  - `Free-azlan` (priority 1, active)
  - `Free-moh.fauzan.azim@gmail.com` (priority 2, active)
- **`backend/app/agent/providers.py`** — ubah default model web:
  - `web_search()` default `search-combo` → **`tavily`** (baris 238)
  - `web_fetch()` default `fetch-combo` → **`tavily`** (baris 256)
- **Root `.env`** — tambah variabel eksplisit:
  - `NINEROUTER_SEARCH_MODEL=tavily`
  - `NINEROUTER_FETCH_MODEL=tavily`
  - (`.env` di-ignore git; backend memuat via `config.py: load_dotenv(ROOT/".env")`)

## Multi-key failover (terverifikasi dari source `/v1/search` route, 9Router 0.5.55)

- Loop pemilih akun: `for(;;){ let a = await c1(provider, triedSet); ... }`.
  Mengambil akun berikutnya yang belum dicoba; jika satu akun rate-limited/kuota
  habis (429) → otomatis pindah akun lain. Semua habis → `All accounts unavailable`.
- Jadi dengan 2+ koneksi Tavily, failover real-time antar key terjadi di sisi 9Router
  tanpa ubah `.env`/kode backend.

## Validasi langsung (backend nyala di port 8000, PID 21000)

| Tes | Hasil |
|---|---|
| `GET /api/v1/ninerouter/status` | `connected` |
| `POST /api/v1/ninerouter/search` (query "berita terbaru Nvidia") | provider **tavily**, hasil terkini Aug 2026, `citation.retrieved_at=2026-08-31` |
| `POST /api/v1/agent/chat` ("cari di web: berita terbaru Nvidia") | agent menjawab lengkap: Q2 FY27 revenue $96,2 M, Jetson Orin Nano 2, Groq 3 LPX + sumber URL |

- Bukti memakai live search: hasil bertanggal 24–26 Agu 2026 (aktual vs hari ini
  31 Agu 2026), berbeda dari fallback `oc/big-pickle` yang halusinasi.
- `usage`: `queries_used=1`, `search_cost_usd=0.008` (kuota free 1000 query/bln).

## Catatan

- `NINEROUTER_WEB_MODEL=cx/gpt-5.6-sol` dipertahankan sebagai fallback cadangan
  `_run_web_llm_answer()` bila `/v1/search` gagal.
- Provider search gratis tanpa key opsional: Brave (2.000/bln), SearXNG (self-host).
- Backend dijalankan via: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

---

# Tambahan 2026-08-31 — Self-host SearXNG (free tier unlimited)

## Tujuan
Menyediakan jalur web search gratis & unlimited di samping Tavily, lewat
instance SearXNG self-hosted yang dipakai 9Router.

## Masalah
- 9Router punya provider `searxng` (freeTier, noAuth, cost 0, quota 999.999/bln),
  tapi butuh instance SearXNG yang berjalan (`baseUrl = SEARXNG_URL ||
  http://localhost:8888/search`). Tanpa instance, `/v1/models/web` tidak menampilkan
  searxng & query `/v1/search` gagal.

## Instalasi
- **Docker Desktop** sebelumnya tidak ada; diinstall secara silent (WSL2 backend):
  `Docker Desktop Installer.exe install --quiet --accept-license --backend=wsl-2
  --always-run-service` (exit 0). PATH tambah `C:\Program Files\Docker\Docker\resources\bin`
  (diperlukan agar `docker-credential-desktop` ditemukan).
- **File setup** (di `searxng/`):
  - `docker-compose.yml` — image `searxng/searxng`, port `8888:8080`, mount `./config`.
  - `config/settings.yml` — wajib `search.formats: [html, json]` + `server.secret_key`
    agar 9Router bisa query format JSON.
  - `.env` — `SEARXNG_SECRET=<random hex>`.
- Start: `docker compose up -d` → container `searxng` up, 0.0.0.0:8888->8080/tcp.
- Di dashboard 9Router: aktifkan provider SearXNG (Media Providers → Web).

## Konfigurasi akhir
- `.env`: `NINEROUTER_SEARCH_MODEL=searxng`, `NINEROUTER_FETCH_MODEL=tavily`.
- `providers.py:238`: default web_search `searxng`; `web_fetch` tetap `tavily`
  (SearXNG hanya support webSearch, tanpa webFetch).

## Validasi (backend port 8000)
| Tes | Hasil |
|---|---|
| `POST /api/v1/ninerouter/search` | provider **searxng**, cost **$0**, 3 hasil live |
| `POST /api/v1/agent/chat` ("cari di web AI") | jawaban live (detik/CNN/SINDO) + URL |
| `POST /api/v1/ninerouter/fetch` (Wikipedia) | provider **tavily** (extract) |

- SearXNG: HTTP 200, `usage.search_cost_usd=0`. Tavily: `0.008`/query.
- Kombinasi optimal sempat **search gratis unlimited (SearXNG) + extract by Tavily**.

---

# PERTIMBANGAN AKHIR 2026-08-31 — SearXNG DIHAPUS, default kembali ke Tavily

Setelah pemakaian lebih lama, **SearXNG self-host ternyata kurang andal** untuk
provider web search default:

- **Timeout 502/504**: 9Router memakai `timeoutMs:1e4` (10s) untuk searxng, sementara
  agregasi SearXNG multi-engine sering melebihi 10s (terutama cold-start) → request gagal.
- **Hasil kosong (0)**: banyak engine publik memblokir instance self-host IP rumah
  (google cse Suspended, brave Suspended, startpage CAPTCHA, duckduckgo connection
  error). Diskonfigurasi engine bermasalah (startpage/brave) mengurangi error, tapi
  hasil tetap fluktuatif dan kadang 0.
- Tool MCP `net_web_search`/`net_web_fetch` terbukti berfungsi — masalahnya murni di
  sisi provider default.

**Tindakan:**
- Hapus total SearXNG: container & network (`docker compose down -v`), image
  (`docker rmi searxng/searxng`), folder `searxng/`, dan referensi di docs.
- **`.env`**: `NINEROUTER_SEARCH_MODEL=tavily`, `NINEROUTER_FETCH_MODEL=tavily` (kembali).
- **`providers.py`**: default web_search kembali `tavily`.
- **Keputusan:** default search = **Tavily** (andal, 2 key failover aktif di 9Router:
  `Free-azlan` & `Free-moh.fauzan.azim@gmail.com`).
