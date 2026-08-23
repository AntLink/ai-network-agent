---
name: gns3-lab
description: Manage GNS3 labs via controller/compute REST API and telnet consoles - node lifecycle, disk interface rules (IDE for vIOS VMDK images), ubridge socket repair, console automation patterns.
compatibility: OpenCode
---

# GNS3 Lab Management

Operate GNS3 topologies programmatically. Learned from a hard-won
recovery session (2026-08-23) where SATA disk emulation silently broke
flash persistence on all Cisco vIOS nodes.

## API Access

| Endpoint | Auth | Use |
|----------|------|-----|
| Controller `http://localhost:3080/v2` | Basic auth from `%APPDATA%\GNS3\2.2\gns3_server.ini` (`user=` / `password=`) | projects, nodes, links, templates |
| Compute inside GNS3 VM `http://<vm-ip>/v2` | none | compute-level ops only; project list may be empty |
| VM SSH | `gns3`/`gns3` | process/disk forensics (`ps aux`, `qemu-img info -U`) |

Key calls:
```
GET  /v2/projects
POST /v2/projects/{pid}/open            # required before node ops if closed
GET  /v2/projects/{pid}/nodes           # status + properties
GET  /v2/projects/{pid}/links           # ACTUAL cabling map (node:adapter/port)
POST /v2/projects/{pid}/nodes/{nid}/stop
POST /v2/projects/{pid}/nodes/{nid}/start
PUT  /v2/projects/{pid}/nodes/{nid}     # body MUST be minimal:
                                        # {"properties": {"hda_disk_interface": "ide"}}
                                        # full-node PUT returns HTTP 500
GET/PUT /v2/templates/{tid}             # template defaults
```

Console ports are gns3server proxies; find real qemu serial ports with
`ps aux | grep qemu | grep ' -name SW1 '`. Node UUIDs live in the
project `.gns3` file; disk overlays at
`/opt/gns3/projects/<pid>/project-files/qemu/<uuid>/hda_disk.qcow2`
(±1 MB COW overlay over base image is NORMAL).

## CRITICAL RULE: Disk Interface

**Cisco vIOS / IOSvL2 built from original VMware VMDK images
(`vmdk.SSA.*`, `vmdk.SPA.*`) have kernels WITHOUT AHCI/SATA drivers.
They must use `hda_disk_interface: ide`.**

Symptoms when wrongly set to sata (boot LOOKS clean!):
```
%Error opening flash0:/ (No such device)
%SW_VLAN-4-IFS_FAILURE ... vlan.dat ... code = 2595
% IOSv: Failed to create/open configuration file for writing: flash:/nvram
0K bytes of ATA System CompactFlash     <-- "0K" = broken
```

- VLAN creation fails, `write memory` prints `[OK]` **while failing
  silently**, config evaporates on next reload.
- Fix: PUT node/template property to `ide`; healthy boot reports a real
  CompactFlash size (e.g. `262144K bytes`).
- GNS3's official `.sata.qcow2` repacked images are the only SATA-safe ones.

## Broken One-Way Links After Process Churn

If interfaces show `connected` but traffic dies one way:
1. Compare packet counters at BOTH ends
   (`show interfaces X | i packets` vs peer). Input stuck = dead socket.
2. MAC table learning works on the receiving side only.
3. Fix: stop + start the two endpoint nodes via API so ubridge rebuilds
   UDP sockets. Do not just kill qemu processes.

## Console Automation Patterns

IOS virtual consoles drop typed input while output is streaming, and an
ENTER sent during a `Password:` prompt becomes an empty password.

Rules (reference implementation: `backend/finalize_sw2_v3.py`,
`backend/phase1_recovery.py`):
1. Send each command only AFTER seeing the prompt; wait for the prompt
   again before the next command (prompt-synced, never fixed sleeps).
2. Never send keepalive ENTER when the last line ends with `:`.
3. Handle initial config wizard: provoke with ENTER, answer `no` on
   `[yes/no]`.
4. `enable` → watch for `Password:` → send password → verify prompt now
   ends with `#`.
5. Answer `[confirm]`/bits prompts via an answers map, not blind timing.

## Verification Checklist After Any Lab Change

1. Boot log: CompactFlash size not `0K`, no SIGNATURE_FAILED/ATA errors.
2. `write memory` then **prove persistence**:
   `show startup-config | include <all key stanzas>` — hostname alone is
   NOT enough; check trunk/access-vlan/ospf lines too.
3. Link health: counters increment on both ends.
4. End-to-end pings between edge clients, not just adjacent hops.
