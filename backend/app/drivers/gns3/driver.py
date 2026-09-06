"""GNS3 Controller/Compute API driver.

Manages GNS3 labs programmatically:
- Controller API (localhost:3080/v2) — projects, nodes, links, templates
- Compute API (GNS3 VM /v2) — compute-level node operations
- Auth: Basic auth from %APPDATA%\\GNS3\\2.2\\gns3_server.ini
"""
import asyncio
import base64
import configparser
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp

from app.core.audit import log_event


def _resolve_console_host(node_host: str | None, controller_url: str | None) -> str | None:
    """Ganti console_host 0.0.0.0/localhost dengan host controller GNS3.

    Saat GNS3 berjalan di server/VM remote (mis. 172.21.0.2), node
    melaporkan console_host='0.0.0.0' karena socket console sebenarnya
    hidup di controller/compute. Hubungkan ke host controller agar telnet
    sampai ke port console yang diteruskan.
    """
    if node_host and node_host not in ("0.0.0.0", "localhost", "::1", ""):
        return node_host
    if controller_url:
        parsed = urlparse(controller_url)
        if parsed.hostname:
            return parsed.hostname
    return node_host


class GNS3Error(Exception):
    pass


class GNS3AuthError(GNS3Error):
    pass


class GNS3NotFound(GNS3Error):
    pass


class GNS3Driver:
    """GNS3 Controller + Compute API client."""

    def __init__(self, config: Dict[str, Any]):
        """
        config keys:
          - controller_url: dari .env GNS3_CONTROLLER_URL (default lokal) atau payload
          - compute_url: "http://<vm-ip>/v2" (optional, for compute ops)
          - username: "admin" (default)
          - password: from gns3_server.ini or explicit
          - verify_ssl: False (default, for self-signed)
        """
        self.controller_url = config.get("controller_url") or os.getenv("GNS3_CONTROLLER_URL", "http://localhost:3080/v2")
        self.compute_url = config.get("compute_url")
        self.username = config.get("username", "admin")
        self.password = config.get("password") or self._load_password_from_ini()
        self.verify_ssl = config.get("verify_ssl", False)
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_header = self._make_auth_header()

    def _load_password_from_ini(self) -> Optional[str]:
        """Read password from %APPDATA%\\GNS3\\2.2\\gns3_server.ini"""
        try:
            ini_path = Path(os.environ.get("APPDATA", "")) / "GNS3" / "2.2" / "gns3_server.ini"
            if ini_path.exists():
                cp = configparser.ConfigParser()
                cp.read(ini_path)
                return cp.get("Server", "password", fallback=None)
        except Exception:
            pass
        return None

    def _make_auth_header(self) -> Dict[str, str]:
        if not self.password:
            return {}
        cred = f"{self.username}:{self.password}".encode()
        token = base64.b64encode(cred).decode()
        return {"Authorization": f"Basic {token}"}

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self._auth_header,
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ------------------------------------------------------------------
    # Generic request helpers
    # ------------------------------------------------------------------
    async def _request(
        self, method: str, url: str, base: str = "controller", **kwargs
    ) -> Any:
        session = await self._get_session()
        base_url = self.compute_url if base == "compute" else self.controller_url
        full = urljoin(base_url.rstrip("/") + "/", url.lstrip("/"))
        async with session.request(method, full, **kwargs) as resp:
            if resp.status == 401:
                raise GNS3AuthError("Authentication failed (check password)")
            if resp.status == 404:
                raise GNS3NotFound(f"{method} {full} not found")
            if resp.status >= 400:
                text = await resp.text()
                raise GNS3Error(f"{method} {full} -> {resp.status}: {text}")
            if resp.content_type == "application/json":
                return await resp.json()
            return await resp.text()

    async def _get(self, url: str, base: str = "controller") -> Any:
        return await self._request("GET", url, base)

    async def _post(self, url: str, json: Any = None, base: str = "controller") -> Any:
        return await self._request("POST", url, base, json=json)

    async def _put(self, url: str, json: Any = None, base: str = "controller") -> Any:
        return await self._request("PUT", url, base, json=json)

    async def _delete(self, url: str, base: str = "controller") -> Any:
        return await self._request("DELETE", url, base)

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    async def list_projects(self) -> List[Dict]:
        return await self._get("projects")

    async def get_project(self, project_id: str) -> Dict:
        return await self._get(f"projects/{project_id}")

    async def create_project(self, name: str, path: Optional[str] = None) -> Dict:
        payload = {"name": name}
        if path:
            payload["path"] = path
        return await self._post("projects", json=payload)

    async def open_project(self, project_id: str) -> Dict:
        return await self._post(f"projects/{project_id}/open")

    async def close_project(self, project_id: str) -> Dict:
        return await self._post(f"projects/{project_id}/close")

    async def delete_project(self, project_id: str) -> None:
        await self._delete(f"projects/{project_id}")

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------
    async def list_nodes(self, project_id: str) -> List[Dict]:
        return await self._get(f"projects/{project_id}/nodes")

    async def get_node(self, project_id: str, node_id: str) -> Dict:
        return await self._get(f"projects/{project_id}/nodes/{node_id}")

    async def create_node(self, project_id: str, node_def: Dict) -> Dict:
        """Create node from template or raw definition."""
        return await self._post(f"projects/{project_id}/nodes", json=node_def)

    async def start_node(self, project_id: str, node_id: str) -> Dict:
        return await self._post(f"projects/{project_id}/nodes/{node_id}/start")

    async def stop_node(self, project_id: str, node_id: str) -> Dict:
        return await self._post(f"projects/{project_id}/nodes/{node_id}/stop")

    async def restart_node(self, project_id: str, node_id: str) -> Dict:
        await self.stop_node(project_id, node_id)
        await asyncio.sleep(1)
        return await self.start_node(project_id, node_id)

    async def reload_docker_node(self, project_id: str, node_id: str) -> Dict:
        """Recreate a Docker node through the GNS3 compute Docker API."""
        return await self._post(f"compute/projects/{project_id}/docker/nodes/{node_id}/reload")

    async def stop_docker_node(self, project_id: str, node_id: str) -> Dict:
        return await self._post(f"compute/projects/{project_id}/docker/nodes/{node_id}/stop")

    async def start_docker_node(self, project_id: str, node_id: str) -> Dict:
        return await self._post(f"compute/projects/{project_id}/docker/nodes/{node_id}/start")

    async def delete_docker_node_instance(self, project_id: str, node_id: str) -> None:
        """Delete only the compute-side Docker container instance.

        The controller node and its project topology remain intact.  This is
        useful when a Docker image or bootstrap command changed and GNS3's
        start/reload operation retained an already-created container.
        """
        await self._delete(
            f"compute/projects/{project_id}/docker/nodes/{node_id}",
            base="controller",
        )

    async def delete_node(self, project_id: str, node_id: str) -> None:
        await self._delete(f"projects/{project_id}/nodes/{node_id}")

    async def update_node_properties(self, project_id: str, node_id: str, props: Dict) -> Dict:
        """Update node properties (e.g., disk interface, adapters, RAM)."""
        payload = {"properties": props}
        return await self._put(f"projects/{project_id}/nodes/{node_id}", json=payload)

    async def get_node_console(self, project_id: str, node_id: str) -> Dict:
        """Get console connection info (host, port, type).

        GNS3 v2 menyimpan console sebagai field terpisah di node:
        `console` (int port), `console_host`, `console_type`.
        """
        node = await self.get_node(project_id, node_id)
        return {
            "host": _resolve_console_host(node.get("console_host"), self.controller_url),
            "port": node.get("console"),
            "type": node.get("console_type", "telnet"),
        }

    # ------------------------------------------------------------------
    # Links
    # ------------------------------------------------------------------
    async def list_links(self, project_id: str) -> List[Dict]:
        return await self._get(f"projects/{project_id}/links")

    async def create_link(self, project_id: str, link_def: Dict) -> Dict:
        """link_def example:
        {
          "nodes": [
            {"node_id": "uuid1", "adapter_number": 0, "port_number": 0},
            {"node_id": "uuid2", "adapter_number": 0, "port_number": 1}
          ]
        }
        """
        return await self._post(f"projects/{project_id}/links", json=link_def)

    async def delete_link(self, project_id: str, link_id: str) -> None:
        await self._delete(f"projects/{project_id}/links/{link_id}")

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    async def list_templates(self) -> List[Dict]:
        return await self._get("templates")

    async def get_template(self, template_id: str) -> Dict:
        return await self._get(f"templates/{template_id}")

    async def update_template(self, template_id: str, props: Dict) -> Dict:
        """Update template default properties (e.g., disk_interface)."""
        return await self._put(f"templates/{template_id}", json=props)

    # ------------------------------------------------------------------
    # Project snapshots / export
    # ------------------------------------------------------------------
    async def create_snapshot(self, project_id: str, name: str) -> Dict:
        return await self._post(f"projects/{project_id}/snapshots", json={"name": name})

    async def list_snapshots(self, project_id: str) -> List[Dict]:
        return await self._get(f"projects/{project_id}/snapshots")

    async def restore_snapshot(self, project_id: str, snapshot_id: str) -> Dict:
        return await self._post(f"projects/{project_id}/snapshots/{snapshot_id}/restore")

    # ------------------------------------------------------------------
    # Compute-level (optional, needs compute_url)
    # ------------------------------------------------------------------
    async def compute_list_nodes(self) -> List[Dict]:
        if not self.compute_url:
            raise GNS3Error("compute_url not configured")
        return await self._get("nodes", base="compute")

    async def compute_get_node(self, node_id: str) -> Dict:
        if not self.compute_url:
            raise GNS3Error("compute_url not configured")
        return await self._get(f"nodes/{node_id}", base="compute")

    # ------------------------------------------------------------------
    # High-level helpers used by lab recovery
    # ------------------------------------------------------------------
    async def set_node_disk_interface(
        self, project_id: str, node_id: str, interface: str = "ide"
    ) -> Dict:
        """Force disk interface (ide/sata). Minimal PUT body to avoid 500."""
        return await self.update_node_properties(project_id, node_id, {"hda_disk_interface": interface})

    async def wait_node_ready(
        self, project_id: str, node_id: str, timeout: int = 120, interval: int = 3
    ) -> Dict:
        """Poll node status until 'started'."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            node = await self.get_node(project_id, node_id)
            if node.get("status") == "started":
                return node
            await asyncio.sleep(interval)
        raise GNS3Error(f"Node {node_id} not ready after {timeout}s")

    async def full_node_rebuild(
        self, project_id: str, node_id: str, disk_interface: str = "ide"
    ) -> Dict:
        """Stop -> set disk interface -> start -> wait ready."""
        await self.stop_node(project_id, node_id)
        await self.set_node_disk_interface(project_id, node_id, disk_interface)
        await self.start_node(project_id, node_id)
        return await self.wait_node_ready(project_id, node_id)
