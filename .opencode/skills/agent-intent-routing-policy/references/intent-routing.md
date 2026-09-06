# Intent Routing Policy

## Intent schema

```ts
interface AgentIntent {
  type:
    | "how_to_use"
    | "software_task"
    | "linux_admin"
    | "network_readonly"
    | "network_change"
    | "device_inventory"
    | "gns3_topology_generate"
    | "lab_management"
    | "troubleshooting"
    | "clarification"
  targets: Array<{
    kind: "device" | "lab" | "project" | "workspace" | "service" | "topology"
    id?: string
    name?: string
    vendor?: string
  }>
  policy: "READ_ONLY" | "GUARDED" | "APPROVAL_REQUIRED" | "BLOCKED"
  confidence: number
  reason: string
}
```

## Routing rules

`how_to_use`:

```text
cara pakai
cara tambah device
gimana menggunakan terminal
apa itu dry run
kenapa butuh approval
```

Route to user guide, no device execution.

`software_task`:

```text
buat fitur
ubah kode
jalankan test
fix bug
cek error build
```

Route to OpenHands SDK workspace tools.

`linux_admin`:

```text
cek service frigate di ubuntu
cek docker
cek port
restart nginx
journalctl
```

Route to Linux tools. Restart/install/edit is approval-required.

`network_readonly`:

```text
cek interface R1
tampilkan routing MK-1
show version SW1
cek ip address R2
```

Route to vendor read-only tools.

`network_change`:

```text
set IP
buat VLAN
konfigurasi OSPF
deploy config
shutdown interface
```

Route to plan/dry-run/approval/vendor tools.

`gns3_topology_generate`:

```text
buatkan topologi GNS3 untuk BGP
generate lab static routing
buat topologi 2 Cisco 1 MikroTik
```

Route to GNS3 template resolver and topology planner.

`device_inventory`:

```text
tambah device
edit IP management device
hapus device
list device
```

Route to devices tools. Create/update/delete usually requires confirmation.

## Ambiguity rules

Ask clarification when:

- device name is partial and matches multiple devices,
- vendor/platform is unknown,
- topology requires a template that is missing,
- operation is risky but target is unclear,
- user asks `jalankan` without a concrete command or target.

Do not silently choose a device when the intent could affect more than one device.

