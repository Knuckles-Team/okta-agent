"""CONCEPT:OK-OS.governance.okta-2 MCP tool for Okta user operations (action-routed)."""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.mcp.common import destructive_blocked, dispatch, parse_params

#: CONCEPT:OK-OS.identity.default Actions gated behind allow_destructive.
DESTRUCTIVE_USER_ACTIONS = {
    "deactivate",
    "suspend",
    "expire_password",
    "reset_password",
    "clear_sessions",
}

USER_ACTIONS = (
    "list, search, get, create, update, activate, deactivate, suspend, "
    "unsuspend, unlock, expire_password, reset_password, list_groups, "
    "list_apps, list_factors, clear_sessions"
)


async def run_users(
    action: str, params_json: str = "{}", allow_destructive: bool = False
) -> Any:
    """Dispatch one users action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {exc}"}}

    blocked = destructive_blocked(action, DESTRUCTIVE_USER_ACTIONS, allow_destructive)
    if blocked:
        return blocked

    client = get_client()
    if action == "list":
        return dispatch(
            lambda: client.list_users(
                q=p.get("q"),
                filter_expr=p.get("filter"),
                search=p.get("search"),
                limit=p.get("limit", 200),
                max_items=p.get("max_items", 1000),
            )
        )
    if action == "search":
        return dispatch(
            lambda: client.search_users(
                conditions=p.get("conditions"),
                joiner=p.get("joiner", "and"),
                q=p.get("q"),
                limit=p.get("limit", 200),
                max_items=p.get("max_items", 1000),
            )
        )
    if action == "get":
        return dispatch(lambda: client.get_user(p["user_id"]))
    if action == "create":
        return dispatch(
            lambda: client.create_user(
                profile=p["profile"],
                credentials=p.get("credentials"),
                group_ids=p.get("group_ids"),
                activate=p.get("activate", True),
            )
        )
    if action == "update":
        return dispatch(
            lambda: client.update_user(
                p["user_id"],
                profile=p.get("profile"),
                credentials=p.get("credentials"),
            )
        )
    if action == "activate":
        return dispatch(
            lambda: client.activate_user(
                p["user_id"], send_email=p.get("send_email", False)
            )
        )
    if action == "deactivate":
        return dispatch(
            lambda: client.deactivate_user(
                p["user_id"], send_email=p.get("send_email", False)
            )
        )
    if action == "suspend":
        return dispatch(lambda: client.suspend_user(p["user_id"]))
    if action == "unsuspend":
        return dispatch(lambda: client.unsuspend_user(p["user_id"]))
    if action == "unlock":
        return dispatch(lambda: client.unlock_user(p["user_id"]))
    if action == "expire_password":
        return dispatch(
            lambda: client.expire_password(
                p["user_id"], temp_password=p.get("temp_password", False)
            )
        )
    if action == "reset_password":
        return dispatch(
            lambda: client.reset_password(
                p["user_id"], send_email=p.get("send_email", True)
            )
        )
    if action == "list_groups":
        return dispatch(
            lambda: client.list_user_groups(
                p["user_id"], max_items=p.get("max_items", 1000)
            )
        )
    if action == "list_apps":
        return dispatch(lambda: client.list_user_apps(p["user_id"]))
    if action == "list_factors":
        return dispatch(lambda: client.list_user_factors(p["user_id"]))
    if action == "clear_sessions":
        return dispatch(
            lambda: client.clear_user_sessions(
                p["user_id"], oauth_tokens=p.get("oauth_tokens", False)
            )
        )
    return {"error": {"message": f"Unknown users action {action!r}."}}


def register_users_tools(mcp: FastMCP) -> None:
    """Register the Okta users tool."""

    @mcp.tool(tags={"users"})
    async def okta_users(
        action: str = Field(description=f"Action to perform. One of: {USER_ACTIONS}."),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON of arguments. list: optional q/filter/search/limit/"
                'max_items. search: {"conditions": [{"field": "status", '
                '"op": "eq", "value": "ACTIVE"}], "joiner": "and"}. '
                'get/lifecycle/credential actions: {"user_id": "..."} plus '
                "options (send_email, temp_password, oauth_tokens). create: "
                '{"profile": {"firstName": ..., "lastName": ..., "email": '
                '..., "login": ...}, "credentials": {...}, "group_ids": '
                '[...], "activate": true}. update: {"user_id": ..., '
                '"profile": {...}}.'
            ),
        ),
        allow_destructive: bool = Field(
            default=False,
            description=(
                "Must be true to run destructive actions: "
                f"{sorted(DESTRUCTIVE_USER_ACTIONS)}."
            ),
        ),
    ) -> Any:
        """Manage Okta users — lifecycle, credentials, groups/apps/factors, sessions.

        Okta Users API:
        https://developer.okta.com/docs/api/openapi/okta-management/management/tag/User/
        """
        return await run_users(action, params_json, allow_destructive)
