"""CONCEPT:AU-KG.ingest.enterprise-source-extractor Native KG ingestion tool for Okta.

Wire-First: lists real Okta objects via the authenticated :class:`~okta_agent.api_client.Api`
client and pushes them into the ONE epistemic-graph knowledge graph as typed OWL nodes
(``:User`` / ``:Group`` / ``:Application``) via :mod:`okta_agent.kg_ingest`. Best-effort —
returns ``{"ingested": None}`` when no engine is reachable, so the connector still runs with
zero KG infrastructure.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.kg_ingest import ingest_apps, ingest_groups, ingest_users
from okta_agent.mcp.common import parse_params

INGEST_ACTIONS = "users, groups, apps, all"


def _records(envelope: Any) -> list[dict[str, Any]]:
    """Unwrap the client envelope ``{"data": [...]}`` into a list of record dicts."""
    data = envelope.get("data") if isinstance(envelope, dict) else envelope
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def run_ingest(action: str, params_json: str = "{}") -> Any:
    """List Okta objects for ``action`` and ingest them as typed KG nodes."""
    try:
        p = parse_params(params_json)
    except ValueError as exc:
        return {"error": {"message": f"Invalid params_json: {type(exc).__name__}"}}

    limit = p.get("limit", 200)
    max_items = p.get("max_items", 1000)
    client = get_client()
    result: dict[str, Any] = {}

    if action in ("users", "all"):
        users = _records(client.list_users(limit=limit, max_items=max_items))
        result["users"] = {"listed": len(users), "ingested": ingest_users(users)}
    if action in ("groups", "all"):
        groups = _records(client.list_groups(limit=limit, max_items=max_items))
        result["groups"] = {"listed": len(groups), "ingested": ingest_groups(groups)}
    if action in ("apps", "all"):
        apps = _records(client.list_apps(limit=limit, max_items=max_items))
        result["apps"] = {"listed": len(apps), "ingested": ingest_apps(apps)}

    if not result:
        return {"error": {"message": f"Unknown ingest action {action!r}."}}
    return result


def register_ingest_tools(mcp: FastMCP) -> None:
    """Register the Okta native-ingestion tool."""

    @mcp.tool(tags={"kg", "misc"})
    async def okta_ingest(
        action: str = Field(
            default="all",
            description=f"What to ingest. One of: {INGEST_ACTIONS}.",
        ),
        params_json: str = Field(
            default="{}",
            description=(
                'JSON of options: {"limit": 200, "max_items": 1000}. '
                "Controls the page size and overall cap of the listing pulled "
                "before ingestion."
            ),
        ),
    ) -> Any:
        """Natively ingest Okta users/groups/apps into epistemic-graph as typed nodes.

        Lists the requested objects via the Okta Management API and pushes them
        (``:User`` / ``:Group`` / ``:Application`` with their provenance) into the
        knowledge graph via the fast engine client. Best-effort: ``ingested`` is
        ``null`` when no engine is reachable.
        CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        return await run_ingest(action, params_json)
