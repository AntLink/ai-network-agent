"""Unit tests for Aruba AOS-CX parsers (no live device needed).

Samples were captured from the CISCO-ARUBA-LAB GNS3 node SW1-ARUBA
(ArubaOS-CX Virtual.10.10.1181, console 172.30.56.191:5002).
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.drivers.aruba.parser import ArubaParser


SHOW_VERSION = """-----------------------------------------------------------------------------
ArubaOS-CX
(c) Copyright Hewlett Packard Enterprise Development LP
-----------------------------------------------------------------------------
Version      : Virtual.10.10.1181
Build Date   :
Build ID     : ArubaOS-CX:Virtual.10.10.1181:1210b2dbabfa:202608270652
Build SHA    : 1210b2dbabfa94e271975551dcbc5f9840447274
Active Image :                               
"""

SHOW_SYSTEM = """Hostname               : switch
System Description     : Virtual.10.10.1181
Vendor                 : Aruba
Product Name           : ABC123 ArubaOS-CX_OVA
Chassis Serial Nbr     : OVAE10F24
Base MAC Address       : 080009-e10f24
ArubaOS-CX Version     : Virtual.10.10.1181
Time Zone              : UTC
Up Time                : 1 hour, 12 minutes
CPU Util (%)           : 5
CPU Util (% avg 1 min) : 5
CPU Util (% avg 5 min) : 6
Memory Usage (%)       : 42
"""

SHOW_INTERFACE_BRIEF = """--------------------------------------------------------------------------------------------------------------
Port      Native  Mode   Type           Enabled Status  Reason                 Speed   Description
VLAN                                                                 (Mb/s)  
--------------------------------------------------------------------------------------------------------------
1/1/1     --      routed --             no      down    Administratively down  --      --
1/1/2     --      routed --             yes     up      No XCVR installed       10G     uplink
mgmt      --      routed --             yes     up      No XCVR installed       --      --
--------------------------------------------------------------------------------------------------------------
"""

SHOW_IP_INTERFACE = """Interface 1/1/1 is down (Administratively down) 
 Admin state is down
 State information: Administratively down
 Hardware: Ethernet, MAC Address: 08:00:09:e1:0f:24 
 IP MTU 1500 
 Encapsulation dot1q ID: 
 No IPv4 address configured 

Interface 1/1/10 is up 
 Admin state is up
 Hardware: Ethernet, MAC Address: 08:00:09:e1:0f:24 
 IP MTU 1500 
 IPv4 address 10.0.0.1/24 
 VRF: default
"""

SHOW_VLAN = """------------------------------------------------------------------------------------------------------------------
VLAN  Name                              Status  Reason                  Type        Interfaces                    
------------------------------------------------------------------------------------------------------------------
1     DEFAULT_VLAN_1                    down    no_member_port          default
100   LV-TEST                            down    no_member_port          static
"""

SHOW_IP_ROUTE = """Displaying ipv4 routes selected for forwarding

[CODE] Kod              Prefix                 Via              Interface            Metric  Distance  Age       
C     192.168.1.0/24        is directly connected 1/1/1               0       0         -
S*    0.0.0.0/0             192.168.1.254         1/1/1               0       1         -
"""

SHOW_ARP = """No ARP entries found.
"""

SHOW_RUNNING_CONFIG = """Current configuration:
!
!Version ArubaOS-CX Virtual.10.10.1181
vlan 1
!
vlan 100
   name LV-TEST
!
interface mgmt
   no shutdown
   ip dhcp
!
interface 1/1/1
   no shutdown
   ip address 10.0.0.1/24
!
hostname switch
!
ip route 10.0.0.0/24 192.168.1.1
"""


def test_parse_version():
    info = ArubaParser.parse_version(SHOW_VERSION)
    assert info["os"] == "AOS-CX"
    assert info["version"] == "Virtual.10.10.1181"
    assert info["build_id"] == "ArubaOS-CX:Virtual.10.10.1181:1210b2dbabfa:202608270652"
    assert info["build_sha"]


def test_parse_system():
    info = ArubaParser.parse_system(SHOW_SYSTEM)
    assert info["hostname"] == "switch"
    assert info["vendor"] == "Aruba"
    assert info["product_name"] == "ABC123 ArubaOS-CX_OVA"
    assert info["serial"] == "OVAE10F24"
    assert info["cpu_util"] == 5
    assert info["cpu_util_1min"] == 5
    assert info["cpu_util_5min"] == 6
    assert info["memory_usage"] == 42
    assert info["uptime"] == "1 hour, 12 minutes"


def test_parse_facts_merge():
    facts = ArubaParser.parse_facts(SHOW_VERSION, SHOW_SYSTEM)
    assert facts["os"] == "AOS-CX"
    assert facts["version"] == "Virtual.10.10.1181"
    assert facts["hostname"] == "switch"


def test_parse_interfaces_brief():
    ifaces = ArubaParser.parse_interfaces_brief(SHOW_INTERFACE_BRIEF)
    assert len(ifaces) == 3
    first = ifaces[0]
    assert first["name"] == "1/1/1"
    assert first["native_vlan"] == "--"
    assert first["mode"] == "routed"
    assert first["enabled"] is False
    assert first["status"] == "down"
    assert first["reason"] == "Administratively down"
    second = ifaces[1]
    assert second["enabled"] is True
    assert second["status"] == "up"
    assert second["description"] == "uplink"


def test_parse_ip_interfaces():
    blocks = ArubaParser.parse_ip_interfaces(SHOW_IP_INTERFACE)
    assert len(blocks) == 2
    assert blocks[0]["name"] == "1/1/1"
    assert blocks[0]["admin_state"] == "down"
    assert blocks[0]["ip_address"] is None
    assert blocks[1]["ip_address"] == "10.0.0.1/24"
    assert blocks[1]["vrf"] == "default"


def test_parse_vlans():
    vlans = ArubaParser.parse_vlans(SHOW_VLAN)
    assert len(vlans) == 2
    assert vlans[0]["vlan_id"] == 1
    assert vlans[1]["vlan_id"] == 100
    assert vlans[1]["name"] == "LV-TEST"
    assert vlans[1]["type"] == "static"


def test_parse_routes():
    routes = ArubaParser.parse_routes(SHOW_IP_ROUTE)
    assert len(routes) == 2
    connected = next(r for r in routes if r["type"] == "connected")
    assert connected["network"] == "192.168.1.0/24"
    assert connected["interface"] == "1/1/1"
    static = next(r for r in routes if r["type"] == "static")
    assert static["next_hop"] == "192.168.1.254"


def test_parse_arp_empty():
    assert ArubaParser.parse_arp(SHOW_ARP) == []


def test_parse_running_config():
    cfg = ArubaParser.parse_running_config(SHOW_RUNNING_CONFIG)
    assert cfg["hostname"] == "switch"
    vlan100 = next(v for v in cfg["vlans"] if v["vlan_id"] == 100)
    assert vlan100["name"] == "LV-TEST"
    mgmt = next(i for i in cfg["interfaces"] if i["name"] == "mgmt")
    assert mgmt["commands"] == ["no shutdown", "ip dhcp"]
    assert "10.0.0.0/24 192.168.1.1" in cfg["routing"]["static_routes"][0]