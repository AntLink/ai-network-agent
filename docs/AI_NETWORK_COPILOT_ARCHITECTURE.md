# AI Network Copilot Architecture

Tanggal: 2026-08-24

Dokumen ini menetapkan arah arsitektur AI agent untuk project AI Network Agent. Targetnya bukan chatbot yang hanya membungkus tombol "run command", tetapi Network Copilot yang bekerja aman melalui workflow:

```text
Plan -> Validate -> Execute -> Verify
```

## Prinsip Utama

- LLM tidak boleh memiliki akses SSH langsung.
- LLM tidak menjalankan command langsung ke Cisco, MikroTik, Aruba, GNS3, Containerlab, atau host lab.
- LLM hanya menghasilkan structured intent, rencana eksekusi, analisis risiko, dan penjelasan.
- Backend network driver yang menerjemahkan intent menjadi command vendor-specific.
- Semua perubahan jaringan harus melewati validasi, dry run, approval, backup, deploy, verify, dan rollback path.
- Provider AI tidak boleh di-hardcode ke satu vendor.

## Provider Abstraction

Backend harus menyediakan abstraction layer untuk model AI:

```text
backend/app/agent/providers/
|-- base.py
|-- openai.py
|-- anthropic.py
|-- deepseek.py
|-- openrouter.py
|-- ollama.py
`-- nvidia_nim.py
```

Settings harus mendukung pemilihan:

- provider
- model
- temperature
- maximum tokens
- base URL jika provider memerlukan endpoint custom
- status koneksi provider

Contoh:

```text
Provider: OpenAI
Model: GPT-5.x

Provider: DeepSeek
Model: DeepSeek-V3

Provider: Ollama
Model: local-model
```

Secret seperti API key hanya boleh disimpan dan dipakai di backend. Frontend tidak boleh menerima kembali secret plaintext.

## Structured Intent

LLM output untuk operasi jaringan harus dikontrak sebagai JSON intent, bukan raw CLI.

Contoh input user:

```text
Set IP GigabitEthernet0/1 R1 menjadi 192.168.10.1/24
```

Contoh intent:

```json
{
  "action": "configure_interface",
  "device_id": "r1",
  "parameters": {
    "interface": "GigabitEthernet0/1",
    "address": "192.168.10.1/24",
    "enabled": true
  }
}
```

Backend driver menerjemahkan intent ini sesuai vendor.

Cisco IOS:

```text
interface GigabitEthernet0/1
 ip address 192.168.10.1 255.255.255.0
 no shutdown
```

MikroTik RouterOS:

```text
/ip address add address=192.168.10.1/24 interface=ether2
```

Aruba AOS-CX:

```text
interface 1/1/1
 ip address 192.168.10.1/24
 no shutdown
```

Catatan: mapping interface human-readable ke interface vendor-specific harus dilakukan oleh backend berdasarkan inventory/facts, bukan ditebak di frontend.

## Internal Agent Tools

Agent boleh meminta backend menjalankan tool internal yang eksplisit dan terkontrol:

- `get_device()`
- `get_interfaces()`
- `get_running_config()`
- `get_routes()`
- `ping()`
- `traceroute()`
- `backup_config()`
- `generate_config()`
- `validate_config()`
- `deploy_config()`
- `rollback()`
- `verify_change()`
- `gns3_get_topology()`
- `containerlab_manage()`

Tool ini adalah backend capability. Frontend hanya mengirim request agent dan merender hasil/status.

## Troubleshooting Workflow

Untuk pertanyaan diagnosis, agent tidak boleh langsung mengubah konfigurasi.

Contoh:

```text
Kenapa R1 tidak bisa ping R2?
```

Alur yang benar:

1. Ambil status interface.
2. Ambil routing table.
3. Jalankan ping atau test connectivity via backend.
4. Cek ARP.
5. Cek ACL/firewall.
6. Cek routing protocol seperti OSPF/BGP jika relevan.
7. Laporkan temuan.
8. Berikan rekomendasi perubahan dengan risk level.
9. Tampilkan `Dry Run` dan `Approve & Execute`.

Contoh hasil:

```text
Saya menemukan Gi0/1 R1 administratively down.

R1 Gi0/1
IP: 10.10.10.1/30
Admin: DOWN
Operational: DOWN

Perbaikan yang disarankan:

interface GigabitEthernet0/1
 no shutdown

Risk: LOW
```

Jika user approve, task berjalan sebagai:

```text
Backup       success
Configure    success
Verify       success
Ping R2      success
Save config  success
```

## Complex Change Workflow

Untuk perubahan kompleks seperti site-to-site IPsec, agent harus membuat execution plan dulu.

Contoh task:

```text
Buat site-to-site IPsec antara R1 dan R2.
```

Contoh execution plan:

1. Collect current configuration.
2. Identify WAN interfaces.
3. Identify local and remote LAN.
4. Check overlapping subnets.
5. Generate crypto policy.
6. Backup R1 and R2.
7. Configure R1.
8. Configure R2.
9. Generate interesting traffic.
10. Verify ISAKMP/IKE SA.
11. Verify IPsec SA.
12. Save configuration.

Agent tidak boleh melewati approval untuk step yang mengubah device.

## Backend Agent API Target

Endpoint final yang disarankan:

- `POST /api/v1/agent/chat`
- `POST /api/v1/agent/plan`
- `POST /api/v1/agent/validate`
- `POST /api/v1/agent/execute`
- `GET /api/v1/agent/tasks/{task_id}`
- `GET /api/v1/agent/tasks/{task_id}/events`
- `GET /api/v1/agent/events`

Streaming memakai SSE untuk event satu arah dari backend ke frontend. Kontrak current stream membawa `start`, `plan`, `device_state`, `approval`, `task_progress`, `command_output`, `verification`, `text`, `done`, dan `error`. WebSocket dapat ditambahkan jika nanti butuh interaksi full duplex.

## Frontend Agent Response Cards

Frontend `/agent` harus mendukung render typed cards, bukan hanya Markdown:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `alert`
- `verification`

Contoh SSE event:

```json
{
  "type": "task_progress",
  "task_id": "task-182",
  "step": "backup",
  "status": "success",
  "message": "Running configuration backed up"
}
```

UI harus merender progress secara eksplisit:

```text
Configure OSPF

success Pre-check
success Backup
running Configuring R1
pending Configuring R2
pending Verify neighbors
pending Save
```

## Safety Gates

Operasi berikut wajib confirmation dan approval:

- deploy config
- rollback
- restore backup
- delete device
- delete lab
- destroy Containerlab lab
- rebuild GNS3 node
- shutdown interface
- ACL/firewall change
- routing/default route change
- credential/user/password change

Approval payload minimal harus memuat:

- task id atau plan id
- target device/lab
- generated command/config
- risk level
- validation result
- backup requirement/status
- identity user yang approve

## Integrasi Dengan Endpoint Saat Ini

Backend saat ini sudah memiliki sebagian fondasi:

- device read endpoints
- Cisco/MikroTik command endpoints
- config plan/apply/rollback
- policy check
- topology
- audit
- GNS3 endpoints

Gap yang perlu ditambahkan untuk Network Copilot:

- provider abstraction
- agent endpoint
- structured intent schema
- tool registry internal
- task execution model
- SSE/WebSocket event stream
- credentials/settings API
- Containerlab API
- Aruba driver/API jika belum tersedia

## Implementasi Bertahap

Tahap integrasi yang disarankan:

1. Tambahkan schema intent, execution plan, agent event, dan provider config di backend.
2. Tambahkan provider abstraction dengan minimal satu provider aktif dan mock provider untuk dev.
3. Tambahkan read-only agent tools untuk inventory, interface, route, config, ping, traceroute.
4. Hubungkan `/agent` frontend ke endpoint plan/chat tanpa execute.
5. Tambahkan validate dan dry run.
6. Tambahkan approval dan execute melalui config governance.
7. Tambahkan SSE untuk progress task dan command output.
8. Tambahkan rollback/verify workflow.

Target akhir: AI menjadi orchestration layer yang aman, sedangkan perubahan real tetap dilakukan oleh backend driver yang bisa divalidasi, diaudit, dan di-rollback.
