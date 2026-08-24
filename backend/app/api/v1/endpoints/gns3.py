"""GNS3 REST API endpoints."""
import configparser
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
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
        "controller_url": "http://localhost:3080/v2",
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
        controller_url=payload.get("controller_url", "http://localhost:3080/v2"),
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
        return await drv.create_link(project_id, nodes)
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
