"""CONCEPT:OK-OS.governance.okta-2 MCP tool for Okta group operations (action-routed)."""

from typing import Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.mcp.common import destructive_blocked, dispatch, parse_params

#: CONCEPT:OK-OS.identity.default Actions gated behind allow_destructive.
DESTRUCTIVE_GROUP_ACTIONS = {"delete", "remove_member", "deactivate_rule"}

GROUP_ACTIONS = (
    "list, search, get, create, update, delete, list_members, add_member, "
    "remove_member, list_rules, create_rule, activate_rule, deactivate_rule"
)


#: One handler per groups action: ``(client, params) -> raw client-call result``.
#: dispatch() wraps the actual call for uniform error handling.
_GROUP_ACTION_HANDLERS: dict[str, Any] = {
    "list": lambda client, p: client.list_groups(
        q=p.get("q"),
        filter_expr=p.get("filter"),
        search=p.get("search"),
        limit=p.get("limit", 200),
        max_items=p.get("max_items", 1000),
    ),
    "search": lambda client, p: client.search_groups(
        conditions=p.get("conditions"),
        joiner=p.get("joiner", "and"),
        q=p.get("q"),
        limit=p.get("limit", 200),
        max_items=p.get("max_items", 1000),
    ),
    "get": lambda client, p: client.get_group(p["group_id"]),
    "create": lambda client, p: client.create_group(
        p["name"], description=p.get("description")
    ),
    "update": lambda client, p: client.update_group(
        p["group_id"], p["name"], description=p.get("description")
    ),
    "delete": lambda client, p: client.delete_group(p["group_id"]),
    "list_members": lambda client, p: client.list_group_members(
        p["group_id"], max_items=p.get("max_items", 1000)
    ),
    "add_member": lambda client, p: client.add_group_member(
        p["group_id"], p["user_id"]
    ),
    "remove_member": lambda client, p: client.remove_group_member(
        p["group_id"], p["user_id"]
    ),
    "list_rules": lambda client, p: client.list_group_rules(
        search=p.get("search"), max_items=p.get("max_items", 1000)
    ),
    "create_rule": lambda client, p: client.create_group_rule(
        p["name"], p["expression"], p["assign_group_ids"]
    ),
    "activate_rule": lambda client, p: client.activate_group_rule(p["rule_id"]),
    "deactivate_rule": lambda client, p: client.deactivate_group_rule(p["rule_id"]),
}


async def run_groups(
    action: str, params_json: str = "{}", allow_destructive: bool = False
) -> Any:
    """Dispatch one groups action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {type(exc).__name__}"}}

    blocked = destructive_blocked(action, DESTRUCTIVE_GROUP_ACTIONS, allow_destructive)
    if blocked:
        return blocked

    client = get_client()
    handler = _GROUP_ACTION_HANDLERS.get(action)
    if handler is None:
        return {"error": {"message": f"Unknown groups action {action!r}."}}
    return dispatch(lambda: handler(client, p))


def register_groups_tools(mcp: FastMCP) -> None:
    """Register the Okta groups tool."""

    @mcp.tool(
        tags={"groups"},
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
    async def okta_groups(
        action: Literal[
            "activate_rule",
            "add_member",
            "create",
            "create_rule",
            "deactivate_rule",
            "delete",
            "get",
            "list",
            "list_members",
            "list_rules",
            "remove_member",
            "search",
            "update",
        ] = Field(description=f"Action to perform. One of: {GROUP_ACTIONS}."),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON of arguments. list/search: optional q/filter/search/"
                'conditions/limit/max_items. get/delete: {"group_id": "..."}. '
                'create/update: {"name": ..., "description": ...}. members: '
                '{"group_id": ..., "user_id": ...}. create_rule: {"name": '
                '..., "expression": "user.department==\\"Eng\\"", '
                '"assign_group_ids": [...]}. rule lifecycle: '
                '{"rule_id": "..."}.'
            ),
        ),
        allow_destructive: bool = Field(
            default=False,
            description=(
                "Must be true to run destructive actions: "
                f"{sorted(DESTRUCTIVE_GROUP_ACTIONS)}."
            ),
        ),
    ) -> Any:
        """Manage Okta groups — CRUD, membership, and dynamic group rules.

        Okta Groups API:
        https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Group/
        """
        return await run_groups(action, params_json, allow_destructive)
