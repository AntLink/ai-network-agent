# Devices Guide

Route:

```text
/devices
```

Use this page to manage the device inventory used by the agent.

Add device fields:

```text
id
hostname
management_address
vendor
platform
transport
status
device_type
console_host
console_port
```

Common vendor/platform values:

```text
Cisco IOSv:
vendor=cisco
platform=ios
transport=ssh

Cisco IOSvL2:
vendor=cisco
platform=ios-l2
transport=ssh

MikroTik CHR:
vendor=mikrotik
platform=routeros
transport=ssh

Linux Ubuntu:
vendor=linux
platform=ubuntu
transport=ssh

Aruba AOS-CX:
vendor=aruba
platform=aos-cx
transport=ssh
```

After a device is added:

- it appears in `/devices`,
- it becomes available to `/agent`,
- terminal can connect if transport is SSH and credentials are correct,
- device detail pages can request health, facts, interfaces, routes, config, and services.

Ask the agent:

```text
cek health device baru
cek interface device <hostname>
cek service ssh di <hostname>
```

Safety:

- Listing and checking devices is read-only.
- Adding, editing, and deleting devices should require confirmation when done through chat.
- Deleting devices does not delete the real device, only the inventory entry.

