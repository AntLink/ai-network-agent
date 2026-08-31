"""Topology endpoint — serves the saved topology snapshot or generates one from GNS3."""
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import Any, Optional

from app.schemas.gns3 import GNS3Config, GNS3_DEFAULT_CONTROLLER
from app.drivers.gns3.driver import GNS3Driver, GNS3Error

router = APIRouter()
TOPOLOGY_FILE = Path(__file__).resolve().parents[4] / "logs" / "topology.json"
TOPOLOGY_FILE_PREFIX = "topology-"


def _topology_snapshot_file(project_id: str | None = None) -> Path:
    if project_id:
        safe_project_id = "".join(ch for ch in project_id if ch.isalnum() or ch in ("-", "_"))
        return TOPOLOGY_FILE.with_name(f"{TOPOLOGY_FILE_PREFIX}{safe_project_id}.json")
    return TOPOLOGY_FILE


def _detect_vendor(node_type: str, name: str, properties: dict[str, Any]) -> str:
    """Infer vendor from GNS3 node_type, disk image, and node name."""
    node_type_lower = node_type.lower()
    name_lower = name.lower()
    disk_image = properties.get("hda_disk_image", "").lower()

    # Best signal: disk image filename
    if disk_image.startswith("chr") or "routeros" in disk_image:
        return "mikrotik"
    if "vios_l2" in disk_image or "vios" in disk_image or "iosv" in disk_image:
        return "cisco"
    if "aruba" in disk_image or "aoscx" in disk_image:
        return "aruba"

    # Fallback: node name patterns
    if "mikrotik" in name_lower or "chr" in name_lower or "mt" in name_lower or name_lower.startswith("mk"):
        return "mikrotik"
    if "cisco" in name_lower or "iosv" in name_lower:
        return "cisco"
    if "aruba" in name_lower or "aoscx" in name_lower:
        return "aruba"
    if name_lower.startswith("r") and len(name_lower) > 1 and name_lower[1:].isdigit():
        return "cisco"
    if ("switch" in name_lower or name_lower.startswith("sw")) and node_type_lower == "qemu":
        return "cisco"

    # Fallback: node type
    if node_type_lower == "dynamips":
        return "cisco"
    if node_type_lower == "vpcs":
        return "linux"
    if node_type_lower == "cloud":
        return "other"
    if node_type_lower == "qemu":
        return "linux"

    return "other"


def _extract_management_ip(node: dict[str, Any]) -> str:
    """Try to extract a management IP from node properties.

    Skips console_host since that's the GNS3 VM address, not the device IP.
    """
    props = node.get("properties", {})

    for key in ("ip", "management_ip", "mgmt_ip"):
        val = props.get(key)
        if val and isinstance(val, str) and val not in ("0.0.0.0", ""):
            return val

    # For VPCS nodes, check if there's an ip property
    if node.get("node_type") == "vpcs":
        val = props.get("ip")
        if val and isinstance(val, str):
            return val

    return "-"


def _detect_kind(node_type: str, name: str, vendor: str) -> str:
    """Infer a visual kind for topology rendering."""
    node_type_lower = node_type.lower()
    name_lower = name.lower()
    vendor_lower = vendor.lower()

    if "cloud" in name_lower or node_type_lower == "cloud" or name_lower == "nat":
        return "cloud"
    if "loop" in name_lower or "lo" == name_lower:
        return "loopback"
    if "firewall" in name_lower or "fw" in name_lower:
        return "firewall"
    if "switch" in name_lower or name_lower.startswith("sw") or node_type_lower in {"ethernet_switch", "switch"}:
        return "switch"
    if "pc" in name_lower or name_lower.startswith("host") or "server" in name_lower or node_type_lower in {"vpcs", "docker", "qemu"}:
        return "host"
    if "router" in name_lower or name_lower.startswith("r") or vendor_lower in {"cisco", "mikrotik"}:
        return "router"
    return "other"


def _detect_node_type(node_type: str) -> str:
    """Preserve the GNS3 node class for UI differentiation."""
    value = node_type.lower()
    if value in {"qemu", "vpcs", "dynamips", "cloud", "ethernet_switch", "docker"}:
        return value
    return "other"


def _get_port_name(node: dict[str, Any], adapter_number: int, port_number: int) -> str:
    """Get the real port name from GNS3 node ports list, with fallback."""
    for port in node.get("ports", []):
        if port.get("adapter_number") == adapter_number and port.get("port_number") == port_number:
            return port.get("name", f"eth{adapter_number}")
    return f"eth{adapter_number}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_saved_topology(project_id: str | None = None) -> dict[str, Any] | None:
    candidates = []
    if project_id:
        candidates.append(_topology_snapshot_file(project_id))
    if TOPOLOGY_FILE not in candidates:
        candidates.append(TOPOLOGY_FILE)

    for path in candidates:
        try:
            if not path.exists():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                data = payload.get("data")
                if isinstance(data, dict):
                    return payload
                if "nodes" in payload and "links" in payload:
                    return {"data": payload, "saved_at": payload.get("saved_at") or _utc_now()}
        except Exception:
            continue
    return None


def _snapshot_project_id(snapshot: dict[str, Any]) -> str | None:
    data = snapshot.get("data")
    if not isinstance(data, dict):
        return None
    project_id = data.get("project_id") or data.get("projectId")
    return project_id if isinstance(project_id, str) and project_id else None


def _save_topology_snapshot(topology: dict[str, Any], project_id: str | None = None) -> dict[str, Any]:
    if project_id and isinstance(topology, dict):
        topology = {**topology, "project_id": project_id}
    snapshot = {
        "data": topology,
        "saved_at": _utc_now(),
        "source": "saved",
    }
    TOPOLOGY_FILE.parent.mkdir(parents=True, exist_ok=True)
    target = _topology_snapshot_file(project_id)
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    if project_id and target != TOPOLOGY_FILE:
        TOPOLOGY_FILE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
    return snapshot


def _normalize_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if isinstance(data, dict):
        return {
            "data": data,
            "saved_at": payload.get("saved_at") or _utc_now(),
            "source": payload.get("source") or "saved",
        }
    if "nodes" in payload and "links" in payload:
        return {
            "data": payload,
            "saved_at": payload.get("saved_at") or _utc_now(),
            "source": payload.get("source") or "saved",
        }
    return {
        "data": payload,
        "saved_at": payload.get("saved_at") or _utc_now(),
        "source": payload.get("source") or "saved",
    }


@router.get("")
async def topology(
    project_id: Optional[str] = Query(None, description="GNS3 project ID to generate topology from"),
    controller_url: Optional[str] = Query(None, description="GNS3 controller URL"),
    username: Optional[str] = Query(None, description="GNS3 username"),
    password: Optional[str] = Query(None, description="GNS3 password"),
):
    """Auto-generate network topology from a GNS3 project.

    When project_id is provided, always prefers live GNS3 data so node status stays current.
    A saved snapshot is used as a fallback when live data cannot be loaded.
    """
    saved = _load_saved_topology(project_id)

    config = GNS3Config(
        controller_url=controller_url or GNS3_DEFAULT_CONTROLLER,
        username=username or "admin",
        password=password,
    )
    drv = GNS3Driver(config.model_dump())

    try:
        # Resolve project_id if not provided
        if not project_id:
            projects = await drv.list_projects()
            if not projects:
                return {"data": {"id": "empty", "name": "No GNS3 Projects", "nodes": [], "links": []}}
            project_id = projects[0]["project_id"]

        project = await drv.get_project(project_id)
        raw_nodes = await drv.list_nodes(project_id)
        raw_links = await drv.list_links(project_id)

        # Build node lookup: node_id -> node data
        node_lookup: dict[str, dict[str, Any]] = {}
        topology_nodes: list[dict[str, Any]] = []

        for idx, node in enumerate(raw_nodes):
            node_id = node.get("node_id", "")
            name = node.get("name", f"Node {idx + 1}")
            node_type = node.get("node_type", "")
            status = node.get("status", "stopped")
            props = node.get("properties", {})
            vendor = _detect_vendor(node_type, name, props)
            kind = _detect_kind(node_type, name, vendor)
            node_type_label = _detect_node_type(node_type)
            ip = _extract_management_ip(node)

            node_lookup[node_id] = {
                "id": node_id,
                "name": name,
                "type": node_type,
                "raw_node": node,
            }

            topology_nodes.append({
                "id": node_id,
                "hostname": name,
                "vendor": vendor,
                "kind": kind,
                "nodeType": node_type_label,
                "status": "online" if status in ("started", "running") else "offline",
                "ip": ip,
            })

        # Build topology links
        topology_links: list[dict[str, Any]] = []
        for link in raw_links:
            link_id = link.get("link_id", "")
            connected = link.get("nodes", [])
            link_status = link.get("status", "up")

            if len(connected) < 2:
                continue

            a = connected[0]
            b = connected[1]

            raw_a = node_lookup.get(a.get("node_id", ""), {}).get("raw_node", {})
            raw_b = node_lookup.get(b.get("node_id", ""), {}).get("raw_node", {})

            adapter_a = a.get("adapter_number", 0)
            port_a = a.get("port_number", 0)
            adapter_b = b.get("adapter_number", 0)
            port_b = b.get("port_number", 0)

            topology_links.append({
                "id": link_id,
                "source": a.get("node_id", ""),
                "target": b.get("node_id", ""),
                "sourceInterface": _get_port_name(raw_a, adapter_a, port_a),
                "targetInterface": _get_port_name(raw_b, adapter_b, port_b),
                "status": "down" if link_status == "down" else "up",
            })

        project_name = project.get("name", project_id)
        snapshot = {
            "id": f"gns3-{project_id}",
            "name": f"{project_name} Topology",
            "nodes": topology_nodes,
            "links": topology_links,
        }
        _save_topology_snapshot(snapshot, project_id)

        return {
            "data": snapshot,
            "saved_at": _utc_now(),
            "source": "live",
        }

    except GNS3Error as e:
        if saved:
            return _normalize_snapshot(saved)
        raise HTTPException(502, f"GNS3 error: {e}")
    except HTTPException:
        raise
    except Exception as e:
        if saved:
            return _normalize_snapshot(saved)
        raise HTTPException(500, f"Topology generation failed: {e}")
    finally:
        await drv.close()


@router.post("")
async def save_topology(payload: dict[str, Any] | None = None):
    """Persist a topology snapshot as JSON and return it."""
    payload = payload or {}
    topology = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(topology, dict):
        raise HTTPException(400, "Invalid topology payload")
    if "nodes" not in topology or "links" not in topology:
        raise HTTPException(400, "Topology payload must include nodes and links")

    project_id = payload.get("project_id") or payload.get("projectId")
    if not isinstance(project_id, str) or not project_id.strip():
        project_id = None

    return _save_topology_snapshot(topology, project_id)
