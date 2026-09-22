"""CONCEPT:OK-OS.governance.okta-2 MCP tool for Okta application operations (action-routed)."""

from typing import Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.mcp.common import destructive_blocked, dispatch, parse_params

#: CONCEPT:OK-OS.identity.default Actions gated behind allow_destructive.
DESTRUCTIVE_APP_ACTIONS = {"deactivate", "unassign_user", "unassign_group"}

APP_ACTIONS = (
    "list, get, create, update, activate, deactivate, list_users, "
    "assign_user, unassign_user, list_groups, assign_group, unassign_group"
)


#: One handler per apps action: ``(client, params) -> raw client-call result``.
#: dispatch() wraps the actual call for uniform error handling.
_APP_ACTION_HANDLERS: dict[str, Any] = {
    "list": lambda client, p: client.list_apps(
        q=p.get("q"),
        filter_expr=p.get("filter"),
        limit=p.get("limit", 200),
        max_items=p.get("max_items", 1000),
    ),
    "get": lambda client, p: client.get_app(p["app_id"]),
    "create": lambda client, p: client.create_app(
        p["template"],
        p["label"],
        settings=p.get("settings"),
        activate=p.get("activate", True),
    ),
    "update": lambda client, p: client.update_app(p["app_id"], p["app"]),
    "activate": lambda client, p: client.activate_app(p["app_id"]),
    "deactivate": lambda client, p: client.deactivate_app(p["app_id"]),
    "list_users": lambda client, p: client.list_app_users(
        p["app_id"], max_items=p.get("max_items", 1000)
    ),
    "assign_user": lambda client, p: client.assign_user_to_app(
        p["app_id"], p["user_id"], profile=p.get("profile")
    ),
    "unassign_user": lambda client, p: client.unassign_user_from_app(
        p["app_id"], p["user_id"]
    ),
    "list_groups": lambda client, p: client.list_app_groups(
        p["app_id"], max_items=p.get("max_items", 1000)
    ),
    "assign_group": lambda client, p: client.assign_group_to_app(
        p["app_id"], p["group_id"], priority=p.get("priority")
    ),
    "unassign_group": lambda client, p: client.unassign_group_from_app(
        p["app_id"], p["group_id"]
    ),
}


async def run_apps(
    action: str, params_json: str = "{}", allow_destructive: bool = False
) -> Any:
    """Dispatch one apps action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {type(exc).__name__}"}}

    blocked = destructive_blocked(action, DESTRUCTIVE_APP_ACTIONS, allow_destructive)
    if blocked:
        return blocked

    client = get_client()
    handler = _APP_ACTION_HANDLERS.get(action)
    if handler is None:
        return {"error": {"message": f"Unknown apps action {action!r}."}}
    return dispatch(lambda: handler(client, p))


def register_apps_tools(mcp: FastMCP) -> None:
    """Register the Okta apps tool."""

    @mcp.tool(tags={"apps"})
    async def okta_apps(
        action: Literal[
            "activate",
            "assign_group",
            "assign_user",
            "create",
            "deactivate",
            "get",
            "list",
            "list_groups",
            "list_users",
            "unassign_group",
            "unassign_user",
            "update",
        ] = Field(description=f"Action to perform. One of: {APP_ACTIONS}."),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON of arguments. list: optional q/filter/limit/max_items. "
                'get/activate/deactivate: {"app_id": "..."}. create: '
                '{"template": "oidc"|"saml"|"bookmark", "label": "...", '
                '"settings": {...}, "activate": true} — oidc settings: '
                "redirect_uris/grant_types/response_types; saml settings: "
                "sso_acs_url/audience; bookmark settings: url. update: "
                '{"app_id": ..., "app": {full app object}}. assignments: '
                '{"app_id": ..., "user_id"|"group_id": ...}.'
            ),
        ),
        allow_destructive: bool = Field(
            default=False,
            description=(
                "Must be true to run destructive actions: "
                f"{sorted(DESTRUCTIVE_APP_ACTIONS)}."
            ),
        ),
    ) -> Any:
        """Manage Okta applications — CRUD, lifecycle, and user/group assignments.

        Okta Applications API:
        https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Application/
        """
        return await run_apps(action, params_json, allow_destructive)
