"""CONCEPT:OK-OS.governance.okta-2 MCP tool for Okta user operations (action-routed)."""

from typing import Any, Literal

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


#: One handler per users action: ``(client, params) -> raw client-call result``.
#: dispatch() wraps the actual call for uniform error handling.
_USER_ACTION_HANDLERS: dict[str, Any] = {
    "list": lambda client, p: client.list_users(
        q=p.get("q"),
        filter_expr=p.get("filter"),
        search=p.get("search"),
        limit=p.get("limit", 200),
        max_items=p.get("max_items", 1000),
    ),
    "search": lambda client, p: client.search_users(
        conditions=p.get("conditions"),
        joiner=p.get("joiner", "and"),
        q=p.get("q"),
        limit=p.get("limit", 200),
        max_items=p.get("max_items", 1000),
    ),
    "get": lambda client, p: client.get_user(p["user_id"]),
    "create": lambda client, p: client.create_user(
        profile=p["profile"],
        credentials=p.get("credentials"),
        group_ids=p.get("group_ids"),
        activate=p.get("activate", True),
    ),
    "update": lambda client, p: client.update_user(
        p["user_id"], profile=p.get("profile"), credentials=p.get("credentials")
    ),
    "activate": lambda client, p: client.activate_user(
        p["user_id"], send_email=p.get("send_email", False)
    ),
    "deactivate": lambda client, p: client.deactivate_user(
        p["user_id"], send_email=p.get("send_email", False)
    ),
    "suspend": lambda client, p: client.suspend_user(p["user_id"]),
    "unsuspend": lambda client, p: client.unsuspend_user(p["user_id"]),
    "unlock": lambda client, p: client.unlock_user(p["user_id"]),
    "expire_password": lambda client, p: client.expire_password(
        p["user_id"], temp_password=p.get("temp_password", False)
    ),
    "reset_password": lambda client, p: client.reset_password(
        p["user_id"], send_email=p.get("send_email", True)
    ),
    "list_groups": lambda client, p: client.list_user_groups(
        p["user_id"], max_items=p.get("max_items", 1000)
    ),
    "list_apps": lambda client, p: client.list_user_apps(p["user_id"]),
    "list_factors": lambda client, p: client.list_user_factors(p["user_id"]),
    "clear_sessions": lambda client, p: client.clear_user_sessions(
        p["user_id"], oauth_tokens=p.get("oauth_tokens", False)
    ),
}


async def run_users(
    action: str, params_json: str = "{}", allow_destructive: bool = False
) -> Any:
    """Dispatch one users action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {type(exc).__name__}"}}

    blocked = destructive_blocked(action, DESTRUCTIVE_USER_ACTIONS, allow_destructive)
    if blocked:
        return blocked

    client = get_client()
    handler = _USER_ACTION_HANDLERS.get(action)
    if handler is None:
        return {"error": {"message": f"Unknown users action {action!r}."}}
    return dispatch(lambda: handler(client, p))


def register_users_tools(mcp: FastMCP) -> None:
    """Register the Okta users tool."""

    @mcp.tool(
        tags={"users"},
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
        meta={
            "eg.annotations": {"modalities_in": ["text"], "modalities_out": ["text"]}
        },
    )
    async def okta_users(
        action: Literal[
            "activate",
            "clear_sessions",
            "create",
            "deactivate",
            "expire_password",
            "get",
            "list",
            "list_apps",
            "list_factors",
            "list_groups",
            "reset_password",
            "search",
            "suspend",
            "unlock",
            "unsuspend",
            "update",
        ] = Field(description=f"Action to perform. One of: {USER_ACTIONS}."),
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
