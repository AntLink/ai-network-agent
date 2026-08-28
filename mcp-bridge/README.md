# ai-network-agent — MCP Bridge

Jembatan (bridge) antara backend **FastAPI ai-network-agent** dengan dunia
**MCP (Model Context Protocol)**. Melalui bridge ini, AI agent seperti
**OpenHands (Agent Canvas)** atau **opencode** bisa berbicara dengan network
device kamu (Cisco, MikroTik, dst) memakai tool standar MCP — sementara semua
koneksi SSH, kredensial, klasifikasi risiko, dan approval tetap ditangani
backend kamu.

```
┌─────────────────────────┐
│ AI Agent                │
│ (OpenHands / opencode)  │
└───────────┬─────────────┘
            │ MCP (stdio/SSE)
┌───────────▼─────────────┐   REST/HTTP    ┌──────────────────────────┐
│  mcp-bridge (folder ini)│ ─────────────► │ FastAPI backend (8000)   │
│  server.py + bridge/    │                │ driver Cisco/MikroTik/...│
└─────────────────────────┘                └────────────┬─────────────┘
                                                        │ SSH (asyncssh)
                                              Router/Switch (Mikrotik, Cisco, dll)
```

Folder ini **tidak menyimpan kredensial** device apa pun — semua tetap di
backend (`inventory/` + credentials backend-side).

## Persyaratan

- Python 3.10+ (backend ai-network-agent sudah berjalan di `http://127.0.0.1:8000`)
- Backend harus hidup sebelum bridge dipakai

## Setup

```powershell
cd "C:\Users\mohfa\PycharmProjects\ai-network-agent\mcp-bridge"

# Cara 1: sekali klik (jalankan run.bat)
.\run.bat

# Cara 2: manual
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env   # lalu sesuaikan isi .env
.\.venv\Scripts\python.exe server.py
```

Tanpa mengubah apa pun, default sudah mengarah ke `http://127.0.0.1:8000`
(transport `stdio`, cocok untuk klien lokal).

## Daftar MCP Tools

**Inventori & status:**
| Tool | Fungsi |
|------|--------|
| `net_list_devices` | Daftar semua device |
| `net_get_device` | Detail device |
| `net_get_device_health` | Cek reachability SSH |
| `net_get_facts` | Fakta perangkat (versi OS, model) |
| `net_get_interfaces` / `net_get_routes` | Interface & tabel routing |
| `net_get_running_config` | Running-config |
| `net_get_vlans` / `net_get_memory` / `net_get_ntp` | Tampilan lain |

**Operasi device (lewat jalur aman backend):**
| Tool | Fungsi |
|------|--------|
| `net_run_command` | Jalankan 1 CLI command (risiko & approval ditangani backend) |
| `net_validate_config` | Validasi perintah tanpa apply |
| `net_backup_config` | Backup running-config → simpan file + `download_url` (`/api/v1/backups/download/{id}`) |
| `net_execute_agent_tool` | Eksekusi tool internal Network Copilot |
| `net_agent_tools` | Daftar tool internal backend |

**Workflow konfigurasi:**
| Tool | Fungsi |
|------|--------|
| `net_config_plan` | Buat plan (belum dieksekusi), hasil `plan_id` |
| `net_config_apply` | Apply plan (butuh `approved_by`; backup otomatis + verifikasi) |
| `net_config_rollback` | Rollback perubahan |
| `net_list_plans` / `net_get_plan` | Lihat plan |

**Resource vendor (baca saja):**
| Tool | Fungsi |
|------|--------|
| `net_cisco_resources` | version, routes, arp, cpu-memory, acls, cdp-neighbors, dll |
| `net_mikrotik_resources` | firewall-filter/nat/mangle, dhcp-leases, bgp, ospf, ppp-secrets, dll |

**GNS3 & Topologi:**
| Tool | Fungsi |
|------|--------|
| `net_gns3_local_config` / `net_gns3_test_connection` | Deteksi controller lokal & uji koneksi |
| `net_gns3_list_projects` / `net_gns3_get_project` / `net_gns3_create_project` | Kelola project/topologi |
| `net_gns3_open_project` / `net_gns3_close_project` / `net_gns3_delete_project` | Buka/tutup/hapus project |
| `net_gns3_list_nodes` / `net_gns3_create_node` | Lihat/tambah node (berbasis template) |
| `net_gns3_start_node` / `net_gns3_stop_node` / `net_gns3_restart_node` | Start/stop/restart node |
| `net_gns3_set_node_properties` | Ubah properties node (adapter/RAM/qemu_path) |
| `net_gns3_delete_node` | Hapus node |
| `net_gns3_list_links` / `net_gns3_create_link` / `net_gns3_delete_link` | Lihat/tambah/hapus kabel |
| `net_gns3_list_templates` | Daftar template appliance |
| `net_gns3_list_snapshots` / `net_gns3_create_snapshot` | Snapshot project |

`net_gns3_create_node` otomatis mencocokkan nama template → `template_id`, dan
menyertakan `qemu_path` di properties (penting agar node QEMU berhasil dibuat
di GNS3 VM). Parameter opsional `adapters`/`ram` untuk override jumlah port NIC
dan RAM. GNS3 connector default `http://localhost:3080/v2` (user `admin`).

`net_gns3_create_link` memakai `port_a/port_b` sebagai **nomor interface**
(mis. `2` = Ethernet2) → otomatis dikirim sebagai `adapter_number=2, port_number=0`.
Kalau port tidak valid, tool mengembalikan *hint* port valid dari node.

Template yang sudah tersedia di GNS3 VM kamu: **MikroTik CHR 7.22.1**, **Cisco
Router IOSv15.6(2)T**, **Switches IOSv 15.2(4.0.55)E**, **ASAv Firewall**, plus
built-in (Cloud/NAT/VPCS/switch/hub).

**Lainnya:** `net_backend_health` (cek koneksi ke backend), `net_list_backups`.

## Daftarkan ke klien MCP

### opencode — tambahkan ke `opencode.json` project:

```jsonc
{
  "mcp": {
    "ai-network-agent": {
      "type": "stdio",
      "command": "C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\mcp-bridge\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\mcp-bridge\\server.py"]
    }
  }
}
```

### OpenHands (Agent Canvas)

OpenHands bisa memakai bridge ini lewat **SSE** (cara yang paling direkomendasikan) atau direct stdio.

**Cara SSE (disarankan):**
1. Jalankan bridge dalam mode SSE:
   ```powershell
   .\start-sse.bat        # atau: $env:MCP_TRANSPORT="sse"; .\.venv\Scripts\python.exe server.py
   ```
   Bridge akan mendengar di `http://127.0.0.1:8911`.
2. Di **Agent Canvas** buka `Customize > MCP Servers` → **Add** → pilih **SSE**.
3. Isi URL: `http://127.0.0.1:8911/sse`, lalu simpan/aktifkan.
4. Mulai percakapan baru (server baru aktif untuk percakapan baru).

**Cara direct stdio (untuk dev/testing):**
- Tambahkan server stdio di `Customize > MCP Servers`:
  - Command: `<path>\mcp-bridge\.venv\Scripts\python.exe`
  - Args: `<path>\mcp-bridge\server.py`

**Cara config file (`config.toml`):**
```toml
[mcp]
# SSE (jalankan bridge dengan MCP_TRANSPORT=sse dulu)
sse_servers = ["http://127.0.0.1:8911/sse"]

# Direct stdio (alternatif, untuk dev)
# stdio_servers = [
#   {name="ai-network-agent",
#    command="C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\mcp-bridge\\.venv\\Scripts\\python.exe",
#    args=["C:\\Users\\mohfa\\PycharmProjects\\ai-network-agent\\mcp-bridge\\server.py"]}
# ]
```

## Contoh perintah setelah terhubung

> "Backup dulu config router R1 dan R2, lalu tampilkan interface-nya."
> "Buat plan: tambah static route ke 10.0.10.0/24 via 192.168.1.1 di mikrotik-gw. Jangan apply dulu."
> "Apply plan a1b2c3d4, disetujui oleh teknisi ops."
> "Tunjukkan firewall NAT di router lab."
> "Generate topologi GNS3 baru: buat project 'lab-mpls', tambah 2 node Cisco IOSv dan 1 node RouterOS, hubungkan ether0-nya, lalu start semuanya."

Alur generate topologi yang dilakukan agen dari perintah terakhir:
`net_gns3_create_project` → `net_gns3_list_templates` (pilih template) →
`net_gns3_create_node` (x3) → `net_gns3_create_link` (hubungkan) →
`net_gns3_start_node` (x3).

## Alur keamanan

1. Perintah tulis dipisahkan dari perintah baca; backend mengklasifikasi risiko.
2. `config_apply` **wajib** menyertakan `approved_by` — perubahan tidak jalan tanpa persetujuan.
3. `net_run_command` untuk perintah berisiko menengah/tinggi akan dikembalikan backend sebagai `approval_required` (jangan set `approved=True` tanpa yakin).
4. Bridge hanya HTTP → semua kredensial SSH tetap di backend.