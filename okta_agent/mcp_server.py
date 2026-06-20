"""CONCEPT:OKTA-1.3 Main FastMCP server and tool registration."""

import sys
from typing import Any

from agent_utilities.mcp_utilities import (
    create_mcp_server,
    load_config,
    register_tool_surface,
)
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from okta_agent.api_client import Api
from okta_agent.auth import get_client
from okta_agent.mcp import (
    register_apps_tools,
    register_groups_tools,
    register_policies_tools,
    register_system_tools,
    register_users_tools,
)

# Re-exported so register_tool_surface(tools_module=...) auto-discovers them as
# module attributes (and ruff treats the imports as used).
__all__ = [
    "register_apps_tools",
    "register_groups_tools",
    "register_policies_tools",
    "register_system_tools",
    "register_users_tools",
]

__version__ = "0.5.0"
logger = get_logger(name="okta_agent")


def get_mcp_instance() -> tuple[Any, ...]:
    """Build the FastMCP server with all enabled Okta tools registered."""
    load_config()
    args, mcp, middlewares = create_mcp_server(
        name="Okta Agent MCP",
        version=__version__,
        instructions=(
            "Okta Agent MCP Server — enterprise CIAM/SSO operations against "
            "the Okta Management API (users, groups, apps, policies, system "
            "log). Destructive actions require allow_destructive=true."
        ),
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    register_tool_surface(
        mcp,
        client_cls=Api,
        get_client=get_client,
        service="okta-agent",
        tools_module=sys.modules[__name__],
    )

    for mw in middlewares:
        mcp.add_middleware(mw)
    return mcp, args, middlewares


def mcp_server() -> None:
    """Run the Okta MCP server (stdio or streamable-http)."""
    mcp, args, middlewares = get_mcp_instance()
    print(f"Okta Agent MCP v{__version__}", file=sys.stderr)
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    mcp_server()
