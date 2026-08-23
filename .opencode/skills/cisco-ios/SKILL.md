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
