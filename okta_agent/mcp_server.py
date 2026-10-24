"""CONCEPT:OK-OS.governance.okta-2 Main FastMCP server and tool registration."""

from okta_agent.mcp import (
    register_apps_tools,
    register_groups_tools,
    register_ingest_tools,
    register_policies_tools,
    register_system_tools,
    register_users_tools,
)

# Re-exported so register_tool_surface(tools_module=...) auto-discovers them as
# module attributes (and ruff treats the imports as used).
__all__ = [
    "register_apps_tools",
    "register_groups_tools",
    "register_ingest_tools",
    "register_policies_tools",
    "register_system_tools",
    "register_users_tools",
]
