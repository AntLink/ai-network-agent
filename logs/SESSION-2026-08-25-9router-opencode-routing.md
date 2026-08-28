# Session Log: 9Router OpenCode Routing

Tanggal: 2026-08-25

## Fokus

Menyiapkan 9Router lokal Windows sebagai model gateway hemat token/biaya untuk OpenCode.

## Hasil Cek

- 9Router berjalan di `0.0.0.0:20128`.
- Proses berjalan lewat Node.js:
  - `C:\Users\mohfa\AppData\Roaming\npm\node_modules\9router\app\custom-server.js`
- Endpoint OpenAI-compatible aktif:
  - `http://127.0.0.1:20128/v1/models`
- Combo awal:
  - `9router`
  - `GPT-GEMINI`
  - `NVDIA-MODEL`

## Provider/Model Yang Dipakai Sebagai Dasar

- `oc/big-pickle` dipilih sebagai workhorse/default hemat.
- `nvidia/nvidia/nemotron-3-ultra-550b-a55b` dipilih sebagai escalation/reasoning model.
- Kandidat tambahan:
  - `oc/deepseek-v4-flash-free`
  - `cf/@cf/zai-org/glm-4.7-flash`
  - `oc/laguna-s-2.1-free`
  - `nvidia/deepseek-ai/deepseek-v4-flash`
  - `mistral/codestral-latest`
  - `cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`
  - `cf/@cf/moonshotai/kimi-k2.5`

## Combo Baru Yang Dibuat

`opencode-cheap`:

```text
oc/laguna-s-2.1-free
cf/@cf/zai-org/glm-4.7-flash
mistral/codestral-latest
```

`opencode-coder`:

```text
ocg/deepseek-v4-flash
mistral/codestral-latest
cx/gpt-5.4-mini
nvidia/nvidia/nemotron-3-ultra-550b-a55b
```

`opencode-reasoning`:

```text
cx/gpt-5.4-mini
nvidia/nvidia/nemotron-3-ultra-550b-a55b
cf/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b
cf/@cf/moonshotai/kimi-k2.5
ocg/deepseek-v4-flash
```

## Backup

Database 9Router dibackup sebelum perubahan:

```text
C:\Users\mohfa\AppData\Roaming\9router\db\data.sqlite.backup-opencode-20260825-152710
```

Backup tambahan saat menambahkan Codex/OpenCode Go ke combo:

```text
C:\Users\mohfa\AppData\Roaming\9router\db\data.sqlite.backup-paid-combos-20260825-153630
```

Backup tambahan saat memperbaiki combo karena OpenCode error `Failed to send prompt`:

```text
C:\Users\mohfa\AppData\Roaming\9router\db\data.sqlite.backup-fix-opencode-combos-20260825-160231
```

## Paid Provider Smoke Test

- `cx/gpt-5.4-mini`: sukses HTTP 200, reply `ok`.
- `ocg/deepseek-v4-flash`: provider/model sukses dan reply `ok`, tetapi response 9Router menambahkan trailer `data: [DONE]` setelah JSON sehingga parser strict perlu toleransi.

## OpenCode Prompt Error Fix

Gejala:

```text
Failed to send prompt
Unexpected server error. Check server logs for details.
```

Penyebab yang ditemukan dari smoke test 9Router:

- `oc/deepseek-v4-flash-free`: unavailable dari provider.
- `nvidia/deepseek-ai/deepseek-v4-flash`: EOL sejak `2026-08-07T09:00:00Z`.
- `oc/big-pickle`: sempat timeout/sering hanya reasoning output pada short max token.

Perbaikan:

- `opencode-coder` dipindahkan ke `ocg/deepseek-v4-flash` sebagai model pertama.
- `opencode-cheap` dipindahkan ke `oc/laguna-s-2.1-free` sebagai model pertama.
- `opencode-reasoning` dipindahkan ke `cx/gpt-5.4-mini` sebagai model pertama.

Smoke test final:

```text
opencode-cheap     -> ok
opencode-coder     -> ok
opencode-reasoning -> ok
```

## OpenCode CLI Project Tool Fix

Gejala lanjutan saat menjalankan OpenCode CLI:

```text
Failed to send prompt
Unexpected server error. Check server logs for details.
```

Log `opencode run --print-logs` menunjukkan root cause:

```text
Cannot find module '../../src/api-client.js' from '.opencode/tools/policy_check.ts'
```

Penyebab:

- `.opencode/tools/*.ts` dan `.opencode/tools/*.js` masih import compatibility client lama `../../src/api-client.js`.
- File tersebut sempat terhapus saat frontend lama dibersihkan/dimigrasi.

Perbaikan:

- Mengembalikan compatibility shim:

```text
src/api-client.js
```

Fungsi shim:

```text
apiGet(path)
apiPost(path, body)
```

Default backend:

```text
http://127.0.0.1:8000/api/v1
```

Smoke test OpenCode setelah fix:

```text
C:\Users\mohfa\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe run "Reply only: ok" --print-logs
```

Hasil:

```text
ok
```

Catatan CLI path:

- `where opencode` menemukan `C:\Windows\System32\opencode`.
- File tersebut 0 byte dan menyebabkan `opencode` biasa gagal/Access denied.
- Rename file tersebut ditolak oleh permission Windows.
- Workaround yang valid:

```text
C:\Users\mohfa\AppData\Roaming\npm\opencode.cmd
```

atau:

```text
C:\Users\mohfa\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe
```

Catatan tambahan:

- OpenCode masih memberi warning snapshot karena file `nul` di workspace tidak bisa diindex Git, tetapi warning ini tidak memblokir prompt.

## Skill Baru

Dibuat skill:

```text
.opencode/skills/token-efficient-router-engineer/SKILL.md
```

Isi utama:

- mode `STRICT`, `BALANCED`, `DEEP`
- aturan eskalasi cheap -> coder -> reasoning
- context budget
- tool-output budget
- network automation safety
- helper setup combo 9Router

## OpenCode Global Config

Konfigurasi global OpenCode diupdate:

```text
C:\Users\mohfa\.config\opencode\opencode.json
```

Backup sebelum perubahan:

```text
C:\Users\mohfa\.config\opencode\opencode.json.backup-9router-20260825-154219
```

Mapping aktif:

```text
model       = 9router/opencode-coder
small_model = 9router/opencode-cheap
```

Agent mapping global:

```text
explore/explorer -> 9router/opencode-cheap
general/build    -> 9router/opencode-coder
plan/architect   -> 9router/opencode-reasoning
```

Project network agents:

```text
network-planner        -> 9router/opencode-reasoning
network-operator       -> 9router/opencode-reasoning
network-auditor        -> 9router/opencode-reasoning
network-troubleshooter -> 9router/opencode-reasoning
```

## Claude Code CLI

Claude Code CLI ditemukan di:

```text
C:\Users\mohfa\AppData\Roaming\npm\claude.cmd
```

PowerShell wrapper `claude.ps1` diblokir oleh execution policy, jadi smoke test memakai `claude.cmd`.

Settings Claude Code diupdate:

```text
C:\Users\mohfa\.claude\settings.json
```

Backup:

```text
C:\Users\mohfa\.claude\settings.json.backup-9router-20260825-154953
C:\Users\mohfa\.claude\settings.json.backup-model-overrides-20260825-155147
```

Mapping Claude Code:

```text
ANTHROPIC_BASE_URL = http://127.0.0.1:20128/v1
model              = claude-sonnet-4-5-20250929
```

`modelOverrides`:

```text
claude-sonnet-4-5-20250929 -> opencode-coder
claude-opus-4-5-20251101   -> opencode-reasoning
claude-haiku-4-5-20251001  -> opencode-cheap
```

Smoke test:

```text
cmd /c "C:\Users\mohfa\AppData\Roaming\npm\claude.cmd" -p "Reply only: ok"
```

Hasil:

```text
ok
```

Catatan: konfigurasi awal direct combo sempat berfungsi tetapi memunculkan warning `unrecognized_model`. Pola final memakai `modelOverrides`, sehingga warning hilang.

## Validasi

- Skill divalidasi dengan `quick_validate.py`: sukses.
- Combo baru sudah muncul di `/v1/models` sebagai `owned_by=combo`.
- Config global dibaca ulang dengan redaction: API key tidak ditampilkan.
- Provider `9router` mengarah ke `http://127.0.0.1:20128/v1`.
- Claude Code CLI smoke test sukses tanpa warning.

## Catatan Safety

- Tidak membuka atau menampilkan API key/provider secret.
- Script hanya mengubah tabel `combos`.
- Untuk perubahan network automation, workflow tetap harus `Plan -> Validate -> Execute -> Verify`.
