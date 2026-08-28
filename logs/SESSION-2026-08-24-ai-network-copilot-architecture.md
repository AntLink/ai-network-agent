# Session Log: AI Network Copilot Architecture

Tanggal: 2026-08-24

## Fokus

Menetapkan arsitektur AI chat agent agar tidak berkembang menjadi chatbot sederhana dengan tombol run command. Agent harus menjadi Network Copilot yang aman untuk network automation.

## Keputusan Arsitektur

- Agent memakai workflow `Plan -> Validate -> Execute -> Verify`.
- LLM tidak boleh memiliki akses SSH langsung.
- LLM tidak boleh menjalankan CLI vendor langsung.
- LLM hanya menghasilkan structured intent, execution plan, analisis risiko, dan penjelasan.
- Backend network driver yang menerjemahkan intent ke Cisco IOS, MikroTik RouterOS, Aruba AOS-CX, GNS3, dan Containerlab.
- Provider AI tidak boleh di-hardcode ke satu provider.
- API key dan secret provider tetap berada di backend.

## Provider Target

Target abstraction backend:

- OpenAI
- Anthropic
- DeepSeek
- OpenRouter
- Ollama
- NVIDIA NIM

Target folder:

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

## Structured Intent

Contoh intent yang harus dihasilkan LLM:

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

Intent ini diterjemahkan backend menjadi command vendor-specific setelah validasi.

## Internal Agent Tools

Tool internal yang direncanakan:

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

## Frontend Agent Cards

Frontend agent harus mendukung card/event berikut:

- `message`
- `plan`
- `device_state`
- `command_output`
- `config_diff`
- `approval`
- `task_progress`
- `alert`
- `verification`

SSE event contoh:

```json
{
  "type": "task_progress",
  "task_id": "task-182",
  "step": "backup",
  "status": "success",
  "message": "Running configuration backed up"
}
```

## File Yang Diubah

- `docs/AI_NETWORK_COPILOT_ARCHITECTURE.md`
- `docs/FRONTEND_BACKEND_INTEGRATION.md`
- `.opencode/skills/ai-network-agent-backend-integration/SKILL.md`
- `.opencode/skills/ai-network-agent-frontend/SKILL.md`
- `README.md`

## Tahap Lanjut

Tahap integrasi berikutnya sebaiknya dimulai dari backend:

1. Tambahkan schema intent, execution plan, agent event, dan provider config.
2. Tambahkan provider abstraction dengan minimal mock provider dan satu provider real.
3. Tambahkan read-only agent tools.
4. Hubungkan frontend `/agent` ke endpoint plan/chat tanpa execute.
5. Tambahkan validate, dry run, approval, execute, verify, dan SSE task progress.
