"""GNS3 REST API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from app.schemas.gns3 import (
    GNS3Config, ProjectCreate, ProjectAction, NodeCreate, NodeAction,
    NodePropertiesUpdate, NodeDiskInterface, NodeRebuild,
    LinkCreate, LinkDelete, TemplateUpdate,
    ProjectSnapshot, SnapshotRestore
)
from app.drivers.gns3.driver import GNS3Driver, GNS3Error, GNS3AuthError, GNS3NotFound

router = APIRouter(tags=["gns3"])


def get_driver(config: GNS3Config) -> GNS3Driver:
    return GNS3Driver(config.dict())


# ------------------------------------------------------------------
# Connection test
# ------------------------------------------------------------------
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
async def create_project(payload: ProjectCreate, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.create_project(payload.name, payload.path)
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
async def create_node(project_id: str, payload: NodeCreate, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.create_node(project_id, payload.node_def)
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
    project_id: str, node_id: str, payload: NodePropertiesUpdate, config: GNS3Config
):
    drv = get_driver(config)
    try:
        return await drv.update_node_properties(project_id, node_id, payload.properties)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/disk-interface")
async def set_disk_interface(
    project_id: str, node_id: str, payload: NodeDiskInterface, config: GNS3Config
):
    drv = get_driver(config)
    try:
        return await drv.set_node_disk_interface(project_id, node_id, payload.interface)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.post("/projects/{project_id}/nodes/{node_id}/rebuild")
async def rebuild_node(project_id: str, node_id: str, payload: NodeRebuild, config: GNS3Config):
    """Stop -> set disk interface -> start -> wait ready."""
    drv = get_driver(config)
    try:
        return await drv.full_node_rebuild(project_id, node_id, payload.disk_interface)
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.get("/projects/{project_id}/nodes/{node_id}/console")
async def get_node_console(project_id: str, node_id: str, config: GNS3Config):
    drv = get_driver(config)
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
async def create_link(project_id: str, payload: LinkCreate, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.create_link(project_id, payload.nodes)
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
async def list_templates(config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.list_templates()
    except GNS3Error as e:
        raise HTTPException(502, str(e))
    finally:
        await drv.close()


@router.put("/templates/{template_id}")
async def update_template(template_id: str, payload: TemplateUpdate, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.update_template(template_id, payload.properties)
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
async def create_snapshot(project_id: str, payload: ProjectSnapshot, config: GNS3Config):
    drv = get_driver(config)
    try:
        return await drv.create_snapshot(project_id, payload.name)
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