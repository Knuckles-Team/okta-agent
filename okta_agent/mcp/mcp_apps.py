"""CONCEPT:OKTA-1.3 MCP tool for Okta application operations (action-routed)."""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.mcp.common import destructive_blocked, dispatch, parse_params

#: CONCEPT:OKTA-1.4 Actions gated behind allow_destructive.
DESTRUCTIVE_APP_ACTIONS = {"deactivate", "unassign_user", "unassign_group"}

APP_ACTIONS = (
    "list, get, create, update, activate, deactivate, list_users, "
    "assign_user, unassign_user, list_groups, assign_group, unassign_group"
)


async def run_apps(
    action: str, params_json: str = "{}", allow_destructive: bool = False
) -> Any:
    """Dispatch one apps action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {exc}"}}

    blocked = destructive_blocked(action, DESTRUCTIVE_APP_ACTIONS, allow_destructive)
    if blocked:
        return blocked

    client = get_client()
    if action == "list":
        return dispatch(
            lambda: client.list_apps(
                q=p.get("q"),
                filter_expr=p.get("filter"),
                limit=p.get("limit", 200),
                max_items=p.get("max_items", 1000),
            )
        )
    if action == "get":
        return dispatch(lambda: client.get_app(p["app_id"]))
    if action == "create":
        return dispatch(
            lambda: client.create_app(
                p["template"],
                p["label"],
                settings=p.get("settings"),
                activate=p.get("activate", True),
            )
        )
    if action == "update":
        return dispatch(lambda: client.update_app(p["app_id"], p["app"]))
    if action == "activate":
        return dispatch(lambda: client.activate_app(p["app_id"]))
    if action == "deactivate":
        return dispatch(lambda: client.deactivate_app(p["app_id"]))
    if action == "list_users":
        return dispatch(
            lambda: client.list_app_users(
                p["app_id"], max_items=p.get("max_items", 1000)
            )
        )
    if action == "assign_user":
        return dispatch(
            lambda: client.assign_user_to_app(
                p["app_id"], p["user_id"], profile=p.get("profile")
            )
        )
    if action == "unassign_user":
        return dispatch(
            lambda: client.unassign_user_from_app(p["app_id"], p["user_id"])
        )
    if action == "list_groups":
        return dispatch(
            lambda: client.list_app_groups(
                p["app_id"], max_items=p.get("max_items", 1000)
            )
        )
    if action == "assign_group":
        return dispatch(
            lambda: client.assign_group_to_app(
                p["app_id"], p["group_id"], priority=p.get("priority")
            )
        )
    if action == "unassign_group":
        return dispatch(
            lambda: client.unassign_group_from_app(p["app_id"], p["group_id"])
        )
    return {"error": {"message": f"Unknown apps action {action!r}."}}


def register_apps_tools(mcp: FastMCP) -> None:
    """Register the Okta apps tool."""

    @mcp.tool(tags={"apps"})
    async def okta_apps(
        action: str = Field(description=f"Action to perform. One of: {APP_ACTIONS}."),
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
