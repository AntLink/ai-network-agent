# Aruba AOS-CX Config Patterns

## Interface enable and description

```text
interface 1/1/1
    description Uplink-to-R1
    no shutdown
```

## Access VLAN

```text
vlan 10
    name USERS

interface 1/1/10
    no shutdown
    vlan access 10
```

## Trunk VLAN

```text
vlan 10
    name USERS
vlan 20
    name SERVERS

interface 1/1/48
    no shutdown
    vlan trunk native 1
    vlan trunk allowed 10,20
```

## Layer 3 interface

```text
interface 1/1/1
    no shutdown
    ip address 192.168.10.1/24
```

## SVI

```text
vlan 10
    name USERS

interface vlan 10
    ip address 192.168.10.1/24
    no shutdown
```

## Static route

```text
ip route 0.0.0.0/0 192.168.10.254
```

## OSPF example

```text
router ospf 1
    area 0.0.0.0

interface 1/1/1
    ip ospf 1 area 0.0.0.0
```

## Structured intent example

```json
{
  "action": "configure_access_vlan",
  "device_id": "aruba-sw1",
  "parameters": {
    "interface": "1/1/10",
    "vlan_id": 10,
    "vlan_name": "USERS",
    "enabled": true
  }
}
```

