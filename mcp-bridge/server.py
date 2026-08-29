"""MCP server entry point.

Menjembatani FastAPI backend ai-network-agent menjadi tool MCP standar
sehingga OpenHands / opencode / klien MCP lain bisa mengendalikan router
& switch (Cisco, MikroTik, dst) melalui bahasa alami.

Jalankan:
    python server.py                    # transport stdio (default)
    python server.py                    # via env MCP_TRANSPORT=sse
"""
from __future__ import annotations

import logging

from fastmcp import FastMCP

from bridge import config, operations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("ai-network-agent-mcp")

mcp = FastMCP("ai-network-agent")

_TOOLS = [
    operations.net_list_devices,
    operations.net_add_device,
    operations.net_update_device,
    operations.net_delete_device,
    operations.net_console_exec,
    operations.net_console_exec_node,
    operations.net_console_interactive,
    operations.net_get_device,
    operations.net_get_device_health,
    operations.net_get_facts,
    operations.net_get_interfaces,
    operations.net_get_routes,
    operations.net_get_running_config,
    operations.net_get_vlans,
    operations.net_get_memory,
    operations.net_get_ntp,
    operations.net_run_command,
    operations.net_validate_config,
    operations.net_backup_config,
    operations.net_agent_tools,
    operations.net_execute_agent_tool,
    operations.net_list_pending_approvals,
    operations.net_approve_command,
    operations.net_config_plan,
    operations.net_config_apply,
    operations.net_config_rollback,
    operations.net_list_plans,
    operations.net_get_plan,
    operations.net_list_backups,
    operations.net_cisco_resources,
    operations.net_mikrotik_resources,
    operations.net_gns3_local_config,
    operations.net_gns3_test_connection,
    operations.net_gns3_list_projects,
    operations.net_gns3_get_project,
    operations.net_gns3_create_project,
    operations.net_gns3_open_project,
    operations.net_gns3_close_project,
    operations.net_gns3_delete_project,
    operations.net_gns3_list_nodes,
    operations.net_gns3_get_node_console,
    operations.net_gns3_create_node,
    operations.net_gns3_start_node,
    operations.net_gns3_stop_node,
    operations.net_gns3_restart_node,
    operations.net_gns3_set_node_properties,
    operations.net_gns3_delete_node,
    operations.net_gns3_list_links,
    operations.net_gns3_create_link,
    operations.net_gns3_delete_link,
    operations.net_gns3_list_templates,
    operations.net_gns3_list_snapshots,
    operations.net_gns3_create_snapshot,
    operations.net_backend_health,
]

for _tool in _TOOLS:
    mcp.tool()(_tool)


def main() -> None:
    log.info("ai-network-agent MCP bridge siap (backend=%s)", config.BACKEND_URL)
    log.info("Registered tools: %s", operations.tool_summary())

    transport = config.MCP_TRANSPORT.lower()
    if transport == "sse":
        mcp.run(transport="sse", host=config.MCP_HOST, port=config.MCP_PORT)
    elif transport in ("http", "streamable-http"):
        mcp.run(transport="streamable-http", host=config.MCP_HOST, port=config.MCP_PORT)
    else:
        mcp.run()  # stdio


if __name__ == "__main__":
    main()