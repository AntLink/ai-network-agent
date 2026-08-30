"""Parsers for Ruijie RGOS show-command output.

RGOS is Cisco-IOS-like: prompts are `Router#` / `Router(config)#`, pager is
`terminal length 0`, and most `show` commands match IOS formats closely.
Samples verified live on RG-NSE-Router/Switch V1.06 in GNS3.
"""
import re
from typing import Any, Dict, List


class RuijieParser:
    """Parser for Ruijie RGOS structured output."""

    @staticmethod
    def parse_version(raw_text: str) -> Dict[str, Any]:
        """Parse 'show version' (key : value lines)."""
        info: Dict[str, Any] = {
            "description": None,
            "software_version": None,
            "hardware_version": None,
            "serial": None,
            "uptime": None,
            "start_time": None,
            "patch": None,
        }
        if not raw_text:
            return info
        mapping = {
            "system description": "description",
            "system software version": "software_version",
            "system hardware version": "hardware_version",
            "system serial number": "serial",
            "system uptime": "uptime",
            "system start time": "start_time",
            "system patch number": "patch",
        }
        for line in raw_text.replace("\r", "").splitlines():
            line = line.strip()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            if key in mapping:
                info[mapping[key]] = value.strip() or None
        if info.get("software_version"):
            info["os"] = "RGOS"
            info["version"] = info["software_version"]
        return info

    @staticmethod
    def parse_interfaces(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip interface brief'.

        Columns: Interface | IP-Address(Pri) | IP-Address(Sec) | Status | Protocol
        """
        interfaces: List[Dict[str, Any]] = []
        if not raw_text:
            return interfaces
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = line.lower()
            if "interface" in low and ("ip-address" in low or "status" in low):
                continue
            if re.fullmatch(r"[- ]+", stripped):
                continue
            cols = re.split(r"\s{2,}", stripped)
            if len(cols) < 5:
                continue
            ip_pri = cols[1]
            interfaces.append({
                "name": cols[0],
                "ip_address": None if ip_pri.lower() in ("unassigned", "no ip address", "no address", "--") else ip_pri,
                "ip_address_sec": None if cols[2].lower() in ("unassigned", "no ip address", "no address", "--") else cols[2],
                "status": cols[3],
                "protocol": cols[4] if len(cols) > 4 else "",
            })
        return interfaces

    @staticmethod
    def parse_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show ip route' (IOS-compatible)."""
        routes: List[Dict[str, Any]] = []
        if not raw_text:
            return routes
        connected_re = re.compile(
            r"^\s*([A-Za-z*]+)\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+is directly connected,?\s*(.*)$"
        )
        via_re = re.compile(
            r"^\s*([A-Za-z*]+)\s+(\d+\.\d+\.\d+\.\d+(?:/\d+)?)\s+"
            r"(?:\[(\d+)/(\d+)\] )?via\s+(\S+),?\s*(.*)$"
        )
        for line in raw_text.replace("\r", "").splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"(?i)(codes|gateway of last resort)", line):
                continue
            m = connected_re.match(line)
            if m:
                code, network, rest = m.groups()
                routes.append({
                    "code": code.replace("*", ""),
                    "network": network,
                    "type": "connected",
                    "interface": rest.strip().rstrip(",") or "",
                    "next_hop": "-",
                    "distance": 0,
                    "metric": 0,
                })
                continue
            m = via_re.match(line)
            if m:
                code, network, distance, metric, next_hop, rest = m.groups()
                routes.append({
                    "code": code.replace("*", ""),
                    "network": network,
                    "type": "static" if "s" in code.lower() else "dynamic",
                    "next_hop": next_hop.rstrip(","),
                    "interface": rest.strip().rstrip(",") or "",
                    "distance": int(distance) if distance else None,
                    "metric": int(metric) if metric else None,
                })
        return routes

    @staticmethod
    def parse_arp(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show arp' (best effort)."""
        entries: List[Dict[str, Any]] = []
        if not raw_text:
            return entries
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = line.lower()
            if ("protocol" in low and "address" in low) or re.fullmatch(r"[- ]+", stripped):
                continue
            m = re.match(
                r"^(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+([0-9a-fA-F.:-]+)\s+(\S+)\s+(\S+)\s*$", stripped
            )
            if not m:
                m = re.match(
                    r"^(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F.:-]+)\s+(\S+)\s+(\S+)\s*$", stripped
                )
                if m:
                    addr, mac, iface, type_ = m.groups()
                    entries.append({"address": addr, "mac": mac, "interface": iface, "type": type_})
                continue
            addr, age, mac, iface, type_ = m.groups()
            entries.append({"address": addr, "age": age, "mac": mac, "interface": iface, "type": type_})
        return entries

    @staticmethod
    def parse_vlans(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show vlan' (VLAN/Name/Status/Ports)."""
        vlans: List[Dict[str, Any]] = []
        if not raw_text:
            return vlans
        row_re = re.compile(r"^(\d+)\s+(\S+)\s+(\S+)(?:\s+(.*))?$")
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            low = line.lower()
            if ("vlan" in low and "name" in low) or re.fullmatch(r"[-+ ]+", stripped):
                continue
            m = row_re.match(stripped)
            if not m:
                continue
            try:
                vlan_id = int(m.group(1))
            except (TypeError, ValueError):
                continue
            vlans.append({
                "vlan_id": vlan_id,
                "name": m.group(2),
                "status": m.group(3),
                "ports": (m.group(4) or "").strip(),
            })
        return vlans

    @staticmethod
    def parse_interface_status(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show interface status' (L2 switch ports)."""
        entries: List[Dict[str, Any]] = []
        if not raw_text:
            return entries
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            head_tokens = {"interface", "status", "port", "vlan", "duplex", "speed", "type", "name", "admin", "mode"}
            first = stripped.split()[0].lower()
            if first in head_tokens:
                continue
            if re.fullmatch(r"[- ]+", stripped):
                continue
            cols = re.split(r"\s{2,}", stripped)
            if len(cols) < 2:
                cols = stripped.split()
            if len(cols) < 2:
                continue
            entries.append({
                "name": cols[0],
                "status": cols[1],
                "speed": " ".join(cols[2:]) if len(cols) > 2 else "",
            })
        return entries

    @staticmethod
    def parse_running_config(raw_text: str) -> Dict[str, Any]:
        """Parse RGOS running-config into practical JSON sections (IOS-like)."""
        result: Dict[str, Any] = {
            "hostname": None,
            "version": None,
            "interfaces": [],
            "vlans": [],
            "routing": {"static_routes": [], "protocols": []},
            "global": [],
            "sections": [],
        }
        if not raw_text:
            return result
        current: Dict[str, Any] | None = None
        header_re = re.compile(r"^(interface |vlan |ip route|router )")

        def flush():
            nonlocal current
            if not current:
                return
            result["sections"].append(current)
            header = current["header"]
            body = current["commands"]
            if header.startswith("interface "):
                iface: Dict[str, Any] = {
                    "name": header.removeprefix("interface ").strip(),
                    "description": None,
                    "ip_addresses": [],
                    "shutdown": False,
                    "commands": body,
                }
                for cmd in body:
                    if cmd.startswith("description "):
                        iface["description"] = cmd.removeprefix("description ").strip()
                    elif cmd.startswith("ip address "):
                        iface["ip_addresses"].append(cmd.removeprefix("ip address ").strip())
                    elif cmd == "shutdown":
                        iface["shutdown"] = True
                    elif cmd.startswith("switchport access vlan "):
                        iface["access_vlan"] = cmd.removeprefix("switchport access vlan ").strip()
                    elif cmd.startswith("switchport "):
                        iface.setdefault("switchport", []).append(cmd)
                result["interfaces"].append(iface)
            elif header.startswith("vlan "):
                vlan: Dict[str, Any] = {"vlan_id": header.removeprefix("vlan ").strip(), "name": None, "commands": body}
                for cmd in body:
                    if cmd.startswith("name "):
                        vlan["name"] = cmd.removeprefix("name ").strip()
                result["vlans"].append(vlan)
            elif header.startswith("router "):
                result["routing"]["protocols"].append({"name": header, "commands": body})
            elif header.startswith("ip route "):
                result["routing"]["static_routes"].append(header)
            current = None

        for raw_line in raw_text.replace("\r", "").splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped in ("!",) or stripped.startswith(("Building configuration", "Current configuration")):
                continue
            if raw_line.startswith(" ") and current is not None:
                current["commands"].append(stripped)
                continue
            flush()
            if header_re.match(stripped):
                current = {"header": stripped, "commands": []}
                continue
            if stripped.startswith("hostname "):
                result["hostname"] = stripped.removeprefix("hostname ").strip()
            elif stripped.startswith("version "):
                result["version"] = stripped.removeprefix("version ").strip()
            else:
                result["global"].append(stripped)

        flush()
        for vlan in result["vlans"]:
            try:
                vlan["vlan_id"] = int(vlan["vlan_id"])
            except (TypeError, ValueError):
                pass
        return result