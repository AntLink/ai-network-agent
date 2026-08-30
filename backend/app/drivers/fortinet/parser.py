"""Parsers for Fortinet FortiOS show/get outputs (console)."""
import re
from typing import Any, Dict, List


class FortiOSParser:
    """Parser for FortiOS `get system status` / `get system interface`."""

    @staticmethod
    def parse_version(raw_text: str) -> Dict[str, Any]:
        """Parse 'get system status' key: value lines."""
        info: Dict[str, Any] = {}
        for line in raw_text.replace("\r", "").splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            val = value.strip()
            low = key.lower()
            if "version" in low:
                info["version"] = val
            elif "serial" in low:
                info["serial"] = val
            elif low == "hostname":
                info["hostname"] = val
            elif "model" in low:
                info["model"] = val
            elif "uptime" in low:
                info["uptime"] = val
        if info.get("version"):
            info.setdefault("os", "FortiOS")
        return info

    @staticmethod
    def parse_interfaces(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'get system interface' (FortiOS 7.x one-line blocks).

        Block banner: "== [ port1 ]"
        One packed line: "name: port1   mode: dhcp    ip: 0.0.0.0 0.0.0.0   status: up ..."
        """
        interfaces: List[Dict[str, Any]] = []
        if not raw_text:
            return interfaces
        block_name = ""
        for raw_line in raw_text.replace("\r", "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            m = re.match(r"^==\s*\[\s*([^\]]+)\s*\]", line)
            if m:
                block_name = m.group(1).strip()
                continue
            if not line.startswith("name:"):
                continue
            name = str(re.sub(r"^\s*:*\s*", "", line.split(":", 1)[1])).strip().split()[0]
            fields: Dict[str, Any] = {
                "name": name or block_name,
                "block": block_name or "",
                "mode": "",
                "ip": "",
                "network": "",
                "status": "",
                "type": "",
                "mac": "",
            }
            for key in ("mode", "ip", "status", "type", "mac", "alias"):
                pm = re.search(rf"\b{re.escape(key)}:\s*(\S+)", line)
                if pm:
                    if key == "ip":
                        # ip: <addr> <mask>
                        parts = line.split()
                        for i, tok in enumerate(parts):
                            if tok.startswith("ip:") or tok == "ip:":
                                if i + 1 < len(parts):
                                    fields["ip"] = parts[i + 1]
                                if i + 2 < len(parts) and "." in parts[i + 2]:
                                    fields["network"] = parts[i + 2]
                                break
                    else:
                        fields[key] = pm.group(1)
            interfaces.append(fields)
        return interfaces

    @staticmethod
    def parse_static_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'show router static' (edit-blocks) into a list of routes."""
        routes: List[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None
        for line in raw_text.replace("\r", "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            m = re.match(r"^edit\s+(\d+)\s*$", stripped)
            if m:
                if current:
                    routes.append(current)
                current = {"seq": int(m.group(1)), "dst": "", "gateway": "", "device": ""}
                continue
            if current is None:
                continue
            for key, dest in (("dst", "dst"), ("gateway", "gateway"), ("device", "device")):
                km = re.match(rf"^set\s+{key}\s+(.+)$", stripped)
                if km:
                    current[dest] = km.group(1).strip()
        if current:
            routes.append(current)
        return routes

    @staticmethod
    def parse_routes(raw_text: str) -> List[Dict[str, Any]]:
        """Parse 'get router info routing-table all' (FortiOS format).

        Lines like:
          S*  0.0.0.0/0 [1/0] via 10.99.4.1, port1
          C   10.99.4.0/24 is directly connected, port1
          S   10.0.0.0/8 [10/0] via 192.168.1.1, port2
        """
        routes: List[Dict[str, Any]] = []
        if not raw_text:
            return routes
        via_re = re.compile(
            r"^\s*([SCOBRDKI]+)\*?\s+([\dA-Fa-f:./]+)\s+\[(\d+)/(\d+)\]\s+via\s+([\dA-Fa-f:.]+)[,\s]+\s*(\S+)?"
        )
        connected_re = re.compile(
            r"^\s*([SCOBRDKI]+)\*?\s+([\dA-Fa-f:./]+)\s+is directly connected[,\s]+\s*(\S+)?"
        )
        for raw_line in raw_text.replace("\r", "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("Codes"):
                continue
            m = via_re.match(line)
            if m:
                code, prefix, dist, metric, nh, iface = m.groups()
                routes.append({
                    "code": code,
                    "network": prefix,
                    "next_hop": nh,
                    "interface": iface or "",
                    "distance": int(dist),
                    "metric": int(metric),
                    "type": "static" if code.upper() == "S" else "connected" if code.upper() == "C" else "dynamic",
                })
                continue
            m = connected_re.match(line)
            if m:
                code, prefix, iface = m.groups()
                routes.append({
                    "code": code,
                    "network": prefix,
                    "next_hop": "-",
                    "interface": iface or "",
                    "distance": 0,
                    "metric": 0,
                    "type": "connected",
                })
        return routes