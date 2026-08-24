---
name: cisco-ios
description: Knowledge for managing Cisco IOS/IOS-XE devices.
compatibility: OpenCode
---

# Cisco IOS / IOS-XE

Use standardized tools (`device_get_facts`, `device_get_config`, etc.). Do not use raw SSH commands.

## Command Mappings
| Tool | Command |
|------|---------|
| `device_get_facts` | `show version`, `show running-config` (header) |
| `device_get_config` | `show running-config` |
| `device_get_interfaces` | `show interfaces status`, `show ip interface brief` |
| `device_get_routes` | `show ip route` |
| `device_get_vlans` | `show vlan brief` |
| `device_get_topology` | `show cdp neighbors detail` / `show lldp neighbors` |

## Change Planning
- Use `config_plan` with commands like: `interface GigabitEthernet0/1`, `ip address ...`, `vlan 100`, `name Sales`.
- Enter config mode via `configure terminal`.
- Save: `write memory` (only if requested).

## Risk Classification
- LOW: Adding VLAN, creating user, viewing logs.
- HIGH: Management IP, default route, SSH/AAA, ACLs affecting management.

## Rollback
- Use `configure replace` (IOS-XE 16.x+) or manual restore from `config_backup`.

## Virtual IOS (vIOS/IOSvL2 in GNS3) - Lab Specifics

See also `gns3-lab` skill. Hard rules learned 2026-08-23:

- **Disk interface must be IDE** for VMDK-based images (`vmdk.SSA.*`,
  `vmdk.SPA.*`). Their kernels lack AHCI drivers; under SATA the flash
  never mounts: VLAN creation fails, `write memory` shows `[OK]`
  while silently failing, and configs evaporate on reload.
- **Never trust `[OK]` from `write memory`.** Prove persistence:
  `show startup-config | include hostname|router ospf|access vlan|mode trunk`.
- Boot-time health check: a real CompactFlash size (e.g. `262144K bytes`);
  `0K bytes of ATA CompactFlash` = broken flash.
- SSH on lab images is legacy-only (KEX `diffie-hellman-group14-sha1`,
  host key `ssh-rsa`, MAC `hmac-sha1`). Modern clients need explicit
  `+` algorithm flags; asyncssh connects without flags.
- Console automation: prompt-synced sending only; virtual consoles eat
  keystrokes during streaming output; ENTER at a `Password:` prompt
  submits an empty password.
- Initial boot wizard: answer `no` to "Would you like to enter the
  initial configuration dialog?" before any configuration.

## Driver Implementation Notes (2026-08-24)

### Code Structure
The Cisco IOS driver is split across multiple files for maintainability:
- `backend/app/drivers/cisco/base.py` - Common utilities and constants
- `backend/app/drivers/cisco/driver.py` - Async CiscoDriver (primary)
- `backend/app/drivers/cisco/netmiko_driver.py` - Sync NetmikoCiscoDriver
- `backend/app/drivers/cisco/connection.py` - Netmiko connection wrapper
- `backend/app/drivers/cisco/cli.py` - CLI session logic and error parsing
- `backend/app/drivers/cisco/parser.py` - Output parsers for structured JSON responses

### Credential Management (Single Source of Truth)
All credential logic is centralized in `base.py::get_credentials()`:
- Priority: Device-specific env vars > Global env vars > Defaults
- Pattern: `{DEVICE_ID}_USERNAME`, `{DEVICE_ID}_PASSWORD`, `{DEVICE_ID}_SECRET`
- Fallback: `NETWORK_USERNAME`, `NETWORK_PASSWORD`, `NETWORK_SECRET`
- Default: username='admin', password='', secret=password

### SSH Timeout Handling
- Default timeout: 20s (`SSH_COMMAND_TIMEOUT` in config.py)
- **Note**: IOSv in GNS3 may need 30-45s for config operations
- **Console fallback**: All operations automatically fall back to console if SSH times out
- Legacy SSH options required for IOSv 15.6 are in `base.py::IOSV_LEGACY_SSH_OPTIONS`

### API Response Format (2026-08-24)
**All driver methods now return structured JSON:**

```python
# READ methods (GET) -> {"data": <structured>, "raw": "<original_cli_text>"}
{
    "data": <parsed_structured_data>,
    "raw": "<original_cli_text>"
}

# WRITE methods (POST/DELETE/PATCH) -> normalized via write_response helper
{
    "status": "applied",           # applied | deleted | saved | committed | failed
    "operation": "create_vlan",    # driver method name
    "success": true,
    "output": ""                   # raw device output (usually empty / warning)
}
```

**Available Parsers in `parser.py` (IOSParser):**
- `parse_version()` - show version output
- `parse_interfaces_brief()` - show ip interface brief
- `parse_interfaces_detail()` - show interfaces
- `parse_routes()` - show ip route (connected/local/via/default)
- `parse_arp()` - show ip arp
- `parse_cpu_memory()` - show processes cpu + show memory
  (command yang valid: `show processes cpu`, bukan `show processes cpu summary`)
- `parse_access_lists()` - show access-lists
- `parse_cdp_neighbors()` - show cdp neighbors detail
- `parse_nat_translations()` - show ip nat translation
- `parse_vlans_brief()` - show vlan brief
- `parse_logs()` - show logging (syslog/console/monitor/buffer/trap)

**Endpoint JSON convention:**
- READ: `data` berisi structured list/dict, `raw` = CLI asli (untuk debug)
- WRITE: `write_response()` helper di `app/api/v1/endpoints/helpers.py`
  → `{status, operation, success, output}` — TIDAK double-wrap

### Refactoring Best Practices Applied
1. **Extract common logic**: Shared utilities moved to base.py
2. **No code duplication**: Credential logic now in one place only
3. **Backward compatibility**: No changes to external API
4. **Structured responses**: All read methods return parsed JSON
5. **Test coverage**: All utilities tested and verified
