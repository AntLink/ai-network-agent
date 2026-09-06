# Aruba AOS-CX Commands

## Identity and health

```text
show version
show system
show hostname
show running-config
show startup-config
show logging -r
```

## Interfaces

```text
show interface brief
show interface 1/1/1
show interface 1/1/1 transceiver
show interface 1/1/1 statistics
show lldp neighbor-info
show lldp neighbor-info detail
```

## VLAN and switching

```text
show vlan
show vlan <id>
show mac-address-table
show spanning-tree
show spanning-tree interface 1/1/1
```

## Routing

```text
show ip interface
show ip route
show arp
show ip ospf
show ip ospf neighbor
show bgp summary
```

## Management and services

```text
show ntp status
show dns
show ssh server
show user-group
show aaa authentication
```

## Save

```text
write memory
copy running-config startup-config
```

