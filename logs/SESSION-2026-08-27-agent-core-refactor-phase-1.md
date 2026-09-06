# Session 2026-08-27 - Agent Core Refactor Phase 1

## Tujuan

Mempersiapkan perombakan AI Network Agent agar tidak lagi bergantung pada prompt monolitik saja. Tahap ini membuat core backend yang bisa dipakai bertahap untuk pola:

```text
Thinking -> Planning -> Waiting approval -> Running -> Verifying -> Completed/Failed
```

## Prinsip

- Frontend tidak menjalankan SSH, Linux command, atau network automation langsung.
- LLM tidak diberi akses langsung ke credential atau transport.
- Backend menentukan intent, target, risk policy, approval, tool registry, event, dan audit.
- Endpoint lama tetap dipertahankan supaya UI yang sudah ada tidak langsung rusak.

## File Baru

- `backend/app/agent/risk.py`
  - Policy deterministic: `READ_ONLY`, `GUARDED`, `APPROVAL_REQUIRED`, `BLOCKED`.
  - Memisahkan request inspeksi seperti `cek ip address R1` dari request perubahan seperti `set ip address R1 ...`.

- `backend/app/agent/state_machine.py`
  - Kontrak workflow state untuk event backend ke frontend.
  - State: `thinking`, `planning`, `waiting_approval`, `running`, `verifying`, `completed`, `failed`.

- `backend/app/agent/intent_classifier.py`
  - Klasifikasi intent awal:
    - `how_to_use`
    - `software_task`
    - `linux_admin`
    - `network_readonly`
    - `network_change`
    - `device_inventory`
    - `gns3_topology_generate`
    - `lab_management`
    - `troubleshooting`
    - `clarification`
  - Target resolver berbasis inventory.
  - Fallback ambiguity: jika device target ambigu, agent harus klarifikasi.

- `backend/app/agent/tool_registry.py`
  - Structured tool descriptor untuk families:
    - `devices.*`
    - `linux.*`
    - `cisco.*`
    - `mikrotik.*`
    - `aruba.*`
    - `gns3.*`
    - `topology.*`
    - `containerlab.*`
  - Metadata: namespace, input/output schema, policy, evidence type, timeout, rollback support.

- `backend/app/agent/event_bus.py`
  - Builder event untuk `start`, `workflow_state`, dan `tool_output`.

- `backend/app/agent/audit.py`
  - Builder audit record awal.
  - Scrub field sensitif seperti password/token/secret.

- `backend/app/agent/orchestrator.py`
  - Facade `analyze_request()` untuk menggabungkan intent classifier dan tool registry.

## File Diubah

- `backend/app/api/v1/endpoints/agent.py`
  - Event `start` pada `/api/v1/agent/chat/stream` sekarang membawa metadata `analysis`.
  - Endpoint baru `POST /api/v1/agent/analyze` untuk menguji intent tanpa eksekusi device.
  - Endpoint baru `GET /api/v1/agent/tools/registry` untuk membaca structured tool descriptors.

## Validasi

Berhasil:

```bash
python -m py_compile backend/app/agent/risk.py backend/app/agent/state_machine.py backend/app/agent/intent_classifier.py backend/app/agent/tool_registry.py backend/app/agent/event_bus.py backend/app/agent/audit.py backend/app/agent/orchestrator.py backend/app/api/v1/endpoints/agent.py
```

Smoke test:

```text
cek ip address R1
-> network_readonly, READ_ONLY, target cisco-iosv-r1

set ip address R1 192.168.10.1/24
-> network_change, APPROVAL_REQUIRED, target cisco-iosv-r1
```

## Catatan Penting

- Ini belum mengganti seluruh agent loop lama.
- Ini adalah fondasi agar tahap berikutnya bisa mengarahkan chat ke orchestrator/tool registry secara bertahap.
- Resolver lama di `agent.py` masih perlu dipisah dari endpoint monolitik pada fase berikutnya.
- Setelah wiring penuh, request seperti `cek ip address R1` harus hanya mengambil R1, bukan MK-1 atau device lain.

## Tahap Berikutnya

1. Pindahkan resolver device/session dari `agent.py` ke service terpisah.
2. Jadikan `/chat/stream` memakai `analyze_request()` untuk menentukan:
   - target final,
   - tool yang dijalankan,
   - apakah butuh approval,
   - apakah perlu klarifikasi.
3. Implement real tool dispatcher berdasarkan registry.
4. Persist audit record ke log/JSON atau database.
5. Tambahkan frontend rendering untuk `analysis`, `tool_output`, dan approval button yang stabil.
