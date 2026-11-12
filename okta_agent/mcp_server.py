"""CONCEPT:OK-OS.governance.okta-2 Extra MCP tools: native knowledge-graph ingestion.

The SDK derives one typed tool per method of the ``Api`` client (``okta_list_users``,
``okta_deactivate_user``, ...). The ingest tools list real Okta objects through that
client and push them into the knowledge graph as typed nodes (``:User`` / ``:Group`` /
``:Application``) through :mod:`okta_agent.kg_ingest`. They are best-effort: ``ingested``
is ``None`` when no engine is reachable, so the connector still runs with zero KG
infrastructure. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from okta_agent.auth import get_client
from okta_agent.kg_ingest import ingest_apps, ingest_groups, ingest_users

__all__ = ["register_ingest_tools"]


def _records(envelope: Any) -> list[dict[str, Any]]:
    """Unwrap the client envelope ``{"data": [...]}`` into a list of record dicts."""
    data = envelope.get("data") if isinstance(envelope, dict) else envelope
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def _ingest_users(limit: int, max_items: int) -> dict[str, Any]:
    users = _records(get_client().list_users(limit=limit, max_items=max_items))
    return {"listed": len(users), "ingested": await ingest_users(users)}


async def _ingest_groups(limit: int, max_items: int) -> dict[str, Any]:
    groups = _records(get_client().list_groups(limit=limit, max_items=max_items))
    return {"listed": len(groups), "ingested": await ingest_groups(groups)}


async def _ingest_apps(limit: int, max_items: int) -> dict[str, Any]:
    apps = _records(get_client().list_apps(limit=limit, max_items=max_items))
    return {"listed": len(apps), "ingested": await ingest_apps(apps)}


_LIMIT = Field(
    default=200, description="Page size of the listing pulled before ingestion."
)
_MAX_ITEMS = Field(default=1000, description="Overall cap on listed objects.")


def register_ingest_tools(mcp: FastMCP) -> None:
    """Register the Okta native-ingestion tools."""

    @mcp.tool(tags={"kg", "misc"})
    async def okta_ingest_users(
        limit: int = _LIMIT, max_items: int = _MAX_ITEMS
    ) -> dict[str, Any]:
        """Ingest Okta users into the knowledge graph as typed ``:User`` nodes."""
        return await _ingest_users(limit, max_items)

    @mcp.tool(tags={"kg", "misc"})
    async def okta_ingest_groups(
        limit: int = _LIMIT, max_items: int = _MAX_ITEMS
    ) -> dict[str, Any]:
        """Ingest Okta groups into the knowledge graph as typed ``:Group`` nodes."""
        return await _ingest_groups(limit, max_items)

    @mcp.tool(tags={"kg", "misc"})
    async def okta_ingest_apps(
        limit: int = _LIMIT, max_items: int = _MAX_ITEMS
    ) -> dict[str, Any]:
        """Ingest Okta applications into the knowledge graph as typed ``:Application`` nodes."""
        return await _ingest_apps(limit, max_items)

    @mcp.tool(tags={"kg", "misc"})
    async def okta_ingest_all(
        limit: int = _LIMIT, max_items: int = _MAX_ITEMS
    ) -> dict[str, Any]:
        """Ingest Okta users, groups and applications into the knowledge graph."""
        return {
            "users": await _ingest_users(limit, max_items),
            "groups": await _ingest_groups(limit, max_items),
            "apps": await _ingest_apps(limit, max_items),
        }
