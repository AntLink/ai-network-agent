"""Pydantic schemas for GNS3 API requests."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ------------------------------------------------------------------
# Config / Connection
# ------------------------------------------------------------------
class GNS3Config(BaseModel):
    controller_url: str = "http://localhost:3080/v2"
    compute_url: Optional[str] = None
    username: str = "admin"
    password: Optional[str] = None
    verify_ssl: bool = False


# ------------------------------------------------------------------
# Projects
# ------------------------------------------------------------------
class ProjectCreate(BaseModel):
    name: str
    path: Optional[str] = None


class ProjectAction(BaseModel):
    project_id: str


class ProjectSnapshot(BaseModel):
    project_id: str
    name: str


class SnapshotRestore(BaseModel):
    project_id: str
    snapshot_id: str


# ------------------------------------------------------------------
# Nodes
# ------------------------------------------------------------------
class NodeCreate(BaseModel):
    project_id: str
    node_def: Dict[str, Any]  # raw GNS3 node definition


class NodeAction(BaseModel):
    project_id: str
    node_id: str


class NodePropertiesUpdate(BaseModel):
    project_id: str
    node_id: str
    properties: Dict[str, Any]


class NodeDiskInterface(BaseModel):
    project_id: str
    node_id: str
    interface: str = "ide"  # "ide" or "sata"


class NodeRebuild(BaseModel):
    project_id: str
    node_id: str
    disk_interface: str = "ide"


# ------------------------------------------------------------------
# Links
# ------------------------------------------------------------------
class LinkCreate(BaseModel):
    project_id: str
    nodes: List[Dict[str, Any]]  # [{"node_id": "...", "adapter_number": 0, "port_number": 0}, ...]


class LinkDelete(BaseModel):
    project_id: str
    link_id: str


# ------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------
class TemplateUpdate(BaseModel):
    template_id: str
    properties: Dict[str, Any]


# ------------------------------------------------------------------
# Snapshots
# ------------------------------------------------------------------
class SnapshotCreate(BaseModel):
    project_id: str
    name: str