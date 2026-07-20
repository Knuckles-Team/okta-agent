"""CONCEPT:OK-OS.governance.okta-2 MCP tool for Okta policy operations (read + lifecycle only)."""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.mcp.common import destructive_blocked, dispatch, parse_params

#: CONCEPT:OK-OS.identity.default Actions gated behind allow_destructive.
DESTRUCTIVE_POLICY_ACTIONS = {"deactivate", "deactivate_rule"}

POLICY_ACTIONS = (
    "list, get, list_rules, activate, deactivate, activate_rule, deactivate_rule"
)

#: Write actions intentionally out of scope in this release (see module docs
#: in okta_agent.api.api_client_policies).
OUT_OF_SCOPE_POLICY_ACTIONS = {
    "create",
    "update",
    "delete",
    "create_rule",
    "update_rule",
    "delete_rule",
}


async def run_policies(
    action: str, params_json: str = "{}", allow_destructive: bool = False
) -> Any:
    """Dispatch one policies action against the Okta Management API."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {type(exc).__name__}"}}

    if action in OUT_OF_SCOPE_POLICY_ACTIONS:
        return {
            "error": {
                "message": (
                    f"Policy action {action!r} is intentionally out of scope "
                    "in this release: Okta policy documents are deeply nested "
                    "and type-specific, and a malformed write can lock an org "
                    "out. Use list/get/list_rules and the activate/deactivate "
                    "lifecycle actions, or manage policy bodies in the Okta "
                    "Admin Console."
                )
            }
        }

    blocked = destructive_blocked(action, DESTRUCTIVE_POLICY_ACTIONS, allow_destructive)
    if blocked:
        return blocked

    client = get_client()
    if action == "list":
        return dispatch(
            lambda: client.list_policies(
                p["type"],
                status=p.get("status"),
                max_items=p.get("max_items", 1000),
            )
        )
    if action == "get":
        return dispatch(
            lambda: client.get_policy(
                p["policy_id"], with_rules=p.get("with_rules", False)
            )
        )
    if action == "list_rules":
        return dispatch(lambda: client.list_policy_rules(p["policy_id"]))
    if action == "activate":
        return dispatch(lambda: client.activate_policy(p["policy_id"]))
    if action == "deactivate":
        return dispatch(lambda: client.deactivate_policy(p["policy_id"]))
    if action == "activate_rule":
        return dispatch(
            lambda: client.activate_policy_rule(p["policy_id"], p["rule_id"])
        )
    if action == "deactivate_rule":
        return dispatch(
            lambda: client.deactivate_policy_rule(p["policy_id"], p["rule_id"])
        )
    return {"error": {"message": f"Unknown policies action {action!r}."}}


def register_policies_tools(mcp: FastMCP) -> None:
    """Register the Okta policies tool."""

    @mcp.tool(tags={"policies"})
    async def okta_policies(
        action: str = Field(
            description=(
                f"Action to perform. One of: {POLICY_ACTIONS}. Policy/rule "
                "create and update are intentionally out of scope in this "
                "release (read + lifecycle only)."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                'JSON of arguments. list: {"type": "okta_sign_on"|"password"'
                '|"mfa_enroll"|"access_policy", "status": "ACTIVE"?}. '
                'get: {"policy_id": ..., "with_rules": true?}. '
                'list_rules/lifecycle: {"policy_id": ...} plus '
                '{"rule_id": ...} for rule lifecycle.'
            ),
        ),
        allow_destructive: bool = Field(
            default=False,
            description=(
                "Must be true to run destructive actions: "
                f"{sorted(DESTRUCTIVE_POLICY_ACTIONS)}."
            ),
        ),
    ) -> Any:
        """Inspect Okta policies and toggle policy/rule lifecycle.

        Okta Policy API:
        https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Policy/
        """
        return await run_policies(action, params_json, allow_destructive)
