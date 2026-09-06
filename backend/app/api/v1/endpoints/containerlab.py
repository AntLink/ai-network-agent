"""Containerlab management endpoints."""
from datetime import datetime
from fastapi import APIRouter
from typing import Any

router = APIRouter()

_containerlab_labs: list[dict[str, Any]] = []
_containerlab_topologies: list[dict[str, Any]] = []


@router.get("/labs")
async def list_labs():
    return {"labs": _containerlab_labs}


@router.post("/labs/deploy")
async def deploy_lab(payload: dict[str, Any]):
    lab_id = f"clab-{len(_containerlab_labs) % 1000:03d}"
    lab = {
        "id": lab_id,
        "name": payload.get("name", "Unnamed Lab"),
        "topology_file": payload.get("topology_file", ""),
        "status": "deploying",
        "created_at": datetime.utcnow().isoformat(),
        "nodes": [],
    }
    _containerlab_labs.append(lab)
    return lab


@router.post("/labs/{lab_id}/destroy")
async def destroy_lab(lab_id: str):
    global _containerlab_labs
    _containerlab_labs = [l for l in _containerlab_labs if l.get("id") != lab_id]
    return {"status": "destroyed"}


@router.get("/topologies")
async def list_topologies():
    return {"topologies": _containerlab_topologies}


@router.post("/topologies")
async def add_topology(payload: dict[str, Any]):
    topo = {
        "name": payload.get("name", "topology.clab.yml"),
        "content": payload.get("content", ""),
        "status": "valid",
        "updated_at": datetime.utcnow().isoformat(),
    }
    _containerlab_topologies.append(topo)
    return topo
