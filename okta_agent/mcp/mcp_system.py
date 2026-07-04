"""CONCEPT:OK-OS.governance.okta-2 MCP tool for Okta org/system operations (action-routed)."""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.mcp.common import dispatch, parse_params

SYSTEM_ACTIONS = (
    "org, list_authorization_servers, logs, list_authenticators, "
    "list_factors, list_zones"
)


async def run_system(action: str, params_json: str = "{}") -> Any:
    """Dispatch one system action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {exc}"}}

    client = get_client()
    if action == "org":
        return dispatch(client.get_org)
    if action == "list_authorization_servers":
        return dispatch(
            lambda: client.list_authorization_servers(
                max_items=p.get("max_items", 1000)
            )
        )
    if action == "logs":
        return dispatch(
            lambda: client.get_system_log(
                since=p.get("since"),
                until=p.get("until"),
                filter_expr=p.get("filter"),
                q=p.get("q"),
                limit=p.get("limit", 100),
                max_items=p.get("max_items", 1000),
                sort_order=p.get("sort_order"),
            )
        )
    if action == "list_authenticators":
        return dispatch(client.list_authenticators)
    if action == "list_factors":
        return dispatch(client.list_org_factors)
    if action == "list_zones":
        return dispatch(
            lambda: client.list_network_zones(max_items=p.get("max_items", 1000))
        )
    return {"error": {"message": f"Unknown system action {action!r}."}}


def register_system_tools(mcp: FastMCP) -> None:
    """Register the Okta system tool."""

    @mcp.tool(tags={"system"})
    async def okta_system(
        action: str = Field(
            description=f"Action to perform. One of: {SYSTEM_ACTIONS}."
        ),
        params_json: str = Field(
            default="{}",
            description=(
                'JSON of arguments. logs: {"since": "2026-01-01T00:00:00Z", '
                '"until": ..., "filter": \'eventType eq '
                '"user.session.start"\', "q": "keyword", "limit": 100, '
                '"max_items": 1000, "sort_order": "DESCENDING"} — results '
                "are hard-capped at 1000 events per call; resume with the "
                "returned next_cursor. Other list actions accept max_items."
            ),
        ),
    ) -> Any:
        """Inspect the Okta org — settings, auth servers, system log, authenticators, zones.

        Okta System Log API:
        https://developer.okta.com/docs/api/openapi/okta-management/management/tag/SystemLog/
        """
        return await run_system(action, params_json)
