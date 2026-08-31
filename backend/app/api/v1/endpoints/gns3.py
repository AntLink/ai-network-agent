"""GNS3 REST API endpoints."""
import configparser
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from app.schemas.gns3 import (
    GNS3Config, ProjectCreate, ProjectAction, NodeCreate, NodeAction,
    NodePropertiesUpdate, NodeDiskInterface, NodeRebuild,
    LinkCreate, LinkDelete, TemplateUpdate,
    ProjectSnapshot, SnapshotRestore
)
from app.drivers.gns3.driver import GNS3Driver, GNS3Error, GNS3AuthError, GNS3NotFound
from .safety import direct_write_guard

router = APIRouter(tags=["gns3"], dependencies=[Depends(direct_write_guard)])


def load_local_gns3_config() -> dict[str, Any]:
    """Return non-secret GNS3 server config discovered on this Windows host."""
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "GNS3" / "2.2" / "gns3_server.ini",
        Path.home() / ".config" / "GNS3" / "gns3_server.ini",
    ]

    for path in candidates:
        if not path.exists():
            continue
        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")
        if not parser.has_section("Server"):
            continue

        protocol = parser.get("Server", "protocol", fallback="http")
        host = parser.get("Server", "host", fallback="localhost")
        port = parser.get("Server", "port", fallback="3080")
        username = parser.get("Server", "user", fallback="admin")
        password = parser.get("Server", "password", fallback="")
        auth_enabled = parser.getboolean("Server", "auth", fallback=bool(password))

        return {
            "found": True,
            "path": str(path),
            "controller_url": f"{protocol}://{host}:{port}/v2",
            "username": username,
            "auth_enabled": auth_enabled,
            "password_available": bool(password),
        }

    return {
        "found": False,
        "controller_url": os.getenv("GNS3_CONTROLLER_URL", "http://172.21.0.2/v2"),
        "username": "admin",
        "auth_enabled": False,
        "password_available": False,
    }


def get_driver(config: GNS3Config) -> GNS3Driver:
    return GNS3Driver(config.model_dump())


def config_from_payload(payload: dict[str, Any] | None = None) -> GNS3Config:
    """Accept the flat frontend payload as a GNS3Config subset."""
    payload = payload or {}
    return GNS3Config(
        controller_url=payload.get("controller_url") or os.getenv("GNS3_CONTROLLER_URL", "http://172.21.0.2/v2"),
        compute_url=payload.get("compute_url"),
        username=payload.get("username", "admin"),
        password=payload.get("password"),
        verify_ssl=payload.get("verify_ssl", False),
    )


# ------------------------------------------------------------------
# Connection test
# ------------------------------------------------------------------
@router.get("/local-config")
async def get_local_config():
    """Expose local GNS3 connection metadata without leaking the password."""
    return load_local_gns3_config()


@router.post("/test-connection")
async def test_connection(config: GNS3Config):
    """Verify GNS3 controller/compute connectivity."""
    drv = get_driver(config)
    try:
        projects = await drv.list_projects()
        await drv.close()
        return {"status": "ok", "projects_count": len(projects)}
    except GNS3AuthError:
        raise HTTPException(401, "Authentication failed")
    except GNS3Error as e:
        raise HTTPException(502, f"GNS3 error: {e}")
    except Exception as e:
        raise HTTPException(500, f"Unexpected error: {e}")


# ------------------------------------------------------------------
# Projects
# ------------------------------------------------------------------
@router.post("/projects")
async def list_projects(config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.list_projects()
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/create")
async def create_project(payload: dict[str, Any]):
    drv = get_driver(config_from_payload(payload))
    try:
        if not payload.get("name"):
            raise HTTPException(400, "Project name is required")
        return await drv.create_project(payload["name"], payload.get("path"))
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}")
async def get_project(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.get_project(project_id)
    except GNS3NotFound:
        raise HTTPException(404, "Project not found")
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/open")
async def open_project(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.open_project(project_id)
    except GNS3NotFound:
        raise HTTPException(404, "Project not found")
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/close")
async def close_project(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.close_project(project_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        await drv.delete_project(project_id)
        return {"status": "deleted"}
    except GNS3NotFound:
        raise HTTPException(404, "Project not found")
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------
@router.post("/projects/{project_id}/nodes")
async def list_nodes(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.list_nodes(project_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/create")
async def create_node(project_id: str, payload: dict[str, Any]):
    drv = get_driver(config_from_payload(payload))
    try:
        node_def = payload.get("node_def")
        if not isinstance(node_def, dict):
            raise HTTPException(400, "node_def is required")
        return await drv.create_node(project_id, node_def)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/start")
async def start_node(project_id: str, node_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.start_node(project_id, node_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/stop")
async def stop_node(project_id: str, node_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.stop_node(project_id, node_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/restart")
async def restart_node(project_id: str, node_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.restart_node(project_id, node_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/properties")
async def update_node_properties(
    project_id: str, node_id: str, payload: dict[str, Any]
):
    drv = get_driver(config_from_payload(payload))
    try:
        properties = payload.get("properties")
        if not isinstance(properties, dict):
            raise HTTPException(400, "properties is required")
        return await drv.update_node_properties(project_id, node_id, properties)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/disk-interface")
async def set_disk_interface(
    project_id: str, node_id: str, payload: dict[str, Any]
):
    drv = get_driver(config_from_payload(payload))
    try:
        interface = payload.get("interface", "ide")
        return await drv.set_node_disk_interface(project_id, node_id, interface)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/rebuild")
async def rebuild_node(project_id: str, node_id: str, payload: dict[str, Any]):
    """Stop -> set disk interface -> start -> wait ready."""
    drv = get_driver(config_from_payload(payload))
    try:
        return await drv.full_node_rebuild(project_id, node_id, payload.get("disk_interface", "ide"))
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.get("/projects/{project_id}/nodes/{node_id}/console")
async def get_node_console(project_id: str, node_id: str):
    drv = get_driver(GNS3Config())
    try:
        return await drv.get_node_console(project_id, node_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


class NodeConsoleExecRequest(BaseModel):
    command: str
    username: str | None = None
    password: str | None = None
    enable: bool = False
    allow_empty_password: bool = False
    bootstrap_password: str | None = None
    login_timeout: float = 45.0
    pager_off_command: str | None = None


def _infer_pager_off(node: dict) -> str | None:
    """Kira-kira perintah matikan pager dari metadata node GNS3.

    Supaya output panjang (show running-config, dst) TIDAK memicu marker
    pager (<--- More ---> / ---- More ----) di console raw.
    """
    props = node.get("properties") or {}
    image = str(props.get("hda_disk_image") or "").lower()
    name = str(node.get("name") or "").lower()
    if "asav" in image or "asa" in name:
        return "terminal pager 0"
    if "vios" in image or "iosv" in image or "c7200" in image:
        return "terminal length 0"
    return None


@router.post("/projects/{project_id}/nodes/{node_id}/console-exec")
async def node_console_exec(project_id: str, node_id: str, payload: NodeConsoleExecRequest):
    """Eksekusi perintah via console telnet node GNS3 (first-boot friendly).

    Resolve host/port console LANGSUNG dari GNS3 (tidak bergantung inventory),
    lalu jalankan ConsoleTransport dengan param kredensial/initialize opsional.
    Pager dimatikan otomatis bila node adalah ASAv/IOSv (bila belum di-set).
    """
    drv = get_driver(GNS3Config())
    try:
        node = await drv.get_node(project_id, node_id)
        console_host = node.get("console_host")
        console_port = node.get("console")
        if not console_host or not console_port:
            raise HTTPException(400, "Node tidak memiliki console (mis. Cloud/NAT)")
        from app.transports.console import ConsoleTransport
        pager_off = payload.pager_off_command or _infer_pager_off(node)
        ct = ConsoleTransport(
            console_host,
            int(console_port),
            username=payload.username,
            password=payload.password,
            enable=payload.enable,
            allow_empty_password=payload.allow_empty_password,
            bootstrap_password=payload.bootstrap_password,
            login_timeout=payload.login_timeout,
            device_id=node.get("name") or node_id,
            pager_off_command=pager_off,
        )
        try:
            out = await ct.run(payload.command)
        except Exception as e:
            raise HTTPException(502, f"console exec gagal untuk {node.get('name') or node_id}: {e}")
        return {
            "project_id": project_id,
            "node_id": node_id,
            "node": node.get("name"),
            "console": {"host": console_host, "port": console_port},
            "command": payload.command,
            "output": out,
        }
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


class NodeConsoleScriptRequest(BaseModel):
    command: str
    answers: list[dict[str, str]] = Field(default_factory=list)
    timeout: float = 60.0
    username: str | None = None
    password: str | None = None
    enable: bool = False
    allow_empty_password: bool = False
    bootstrap_password: str | None = None
    login_timeout: float = 45.0
    pager_off_command: str | None = None


@router.post("/projects/{project_id}/nodes/{node_id}/console-interactive")
async def node_console_interactive(project_id: str, node_id: str, payload: NodeConsoleScriptRequest):
    """Eksekusi perintah + jawab prompt interaktif otomatis (rule pattern->send).

    Berguna untuk step interaktif seperti 'crypto key generate rsa'
    (jawab modulus/confirm) atau 'copy running-config flash0:x'.
    Pager tetap dimatikan otomatis untuk node ASAv/IOSv.
    """
    drv = get_driver(GNS3Config())
    try:
        node = await drv.get_node(project_id, node_id)
        console_host = node.get("console_host")
        console_port = node.get("console")
        if not console_host or not console_port:
            raise HTTPException(400, "Node tidak memiliki console (mis. Cloud/NAT)")
        from app.transports.console import ConsoleTransport
        pager_off = payload.pager_off_command or _infer_pager_off(node)
        ct = ConsoleTransport(
            console_host,
            int(console_port),
            username=payload.username,
            password=payload.password,
            enable=payload.enable,
            allow_empty_password=payload.allow_empty_password,
            bootstrap_password=payload.bootstrap_password,
            login_timeout=payload.login_timeout,
            device_id=node.get("name") or node_id,
            pager_off_command=pager_off,
        )
        try:
            out = await ct.run_scripted(payload.command, payload.answers, timeout=payload.timeout)
        except Exception as e:
            raise HTTPException(502, f"console script gagal untuk {node.get('name') or node_id}: {e}")
        return {
            "project_id": project_id,
            "node_id": node_id,
            "node": node.get("name"),
            "command": payload.command,
            "answers": payload.answers,
            "output": out,
        }
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.delete("/projects/{project_id}/nodes/{node_id}")
async def delete_node(project_id: str, node_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        await drv.delete_node(project_id, node_id)
        return {"status": "deleted"}
    except GNS3NotFound:
        raise HTTPException(404, "Node not found")
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


# ------------------------------------------------------------------
# Links
# ------------------------------------------------------------------
@router.post("/projects/{project_id}/links")
async def list_links(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.list_links(project_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/links/create")
async def create_link(project_id: str, payload: dict[str, Any]):
    drv = get_driver(config_from_payload(payload))
    try:
        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            raise HTTPException(400, "nodes is required")
        return await drv.create_link(project_id, {"nodes": nodes})
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.delete("/projects/{project_id}/links/{link_id}")
async def delete_link(project_id: str, link_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        await drv.delete_link(project_id, link_id)
        return {"status": "deleted"}
    except GNS3NotFound:
        raise HTTPException(404, "Link not found")
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


# ------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------
@router.get("/templates")
async def list_templates():
    drv = get_driver(GNS3Config())
    try:
        return await drv.list_templates()
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.put("/templates/{template_id}")
async def update_template(template_id: str, payload: dict[str, Any]):
    drv = get_driver(config_from_payload(payload))
    try:
        properties = payload.get("properties")
        if not isinstance(properties, dict):
            raise HTTPException(400, "properties is required")
        return await drv.update_template(template_id, properties)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


# ------------------------------------------------------------------
# Snapshots
# ------------------------------------------------------------------
@router.post("/projects/{project_id}/snapshots")
async def list_snapshots(project_id: str, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.list_snapshots(project_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/snapshots/create")
async def create_snapshot(project_id: str, payload: dict[str, Any]):
    drv = get_driver(config_from_payload(payload))
    try:
        if not payload.get("name"):
            raise HTTPException(400, "Snapshot name is required")
        return await drv.create_snapshot(project_id, payload["name"])
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/snapshots/{snapshot_id}/restore")
async def restore_snapshot(
    project_id: str, snapshot_id: str, config: GNS3Config
):
    drv = get_driver(config)
    try:
        return await drv.restore_snapshot(project_id, snapshot_id)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()
