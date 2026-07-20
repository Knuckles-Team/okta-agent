"""Native epistemic-graph ingestion for Okta identity records.

All writes use the required ``agent_utilities.knowledge_graph.memory.native_ingest``
primitive. Nodes use canonical ``node_type`` and edges use canonical ``relationship``;
nodes and edges commit in one native transaction. Missing engine dependencies, rejected
records, conflicts, and transaction failures propagate as ``NativeIngestError``.
"""

from __future__ import annotations

import logging
from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)

logger = logging.getLogger("okta_agent.kg")

_SOURCE = "okta-agent"
_DOMAIN = "okta"


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships in one native transaction."""
    return _native_ingest_entities(
        entities, relationships, source=source, domain=domain, client=client, graph=graph
    )


def _profile(rec: dict[str, Any]) -> dict[str, Any]:
    prof = rec.get("profile")
    return prof if isinstance(prof, dict) else {}


def ingest_users(
    users: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map Okta user records → ``:User`` nodes (+ ``:memberOfGroup`` when groups embedded)."""
    entities: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []
    for user in users or []:
        uid = user.get("id")
        if not uid:
            continue
        prof = _profile(user)
        entities.append(
            {
                "id": f"okta:user:{uid}",
                "node_type": "User",
                "name": " ".join(
                    p for p in (prof.get("firstName"), prof.get("lastName")) if p
                )
                or prof.get("login"),
                "login": prof.get("login"),
                "email": prof.get("email"),
                "status": user.get("status"),
                "created": user.get("created"),
                "lastLogin": user.get("lastLogin"),
                "externalToolId": str(uid),
            }
        )
        for grp in user.get("groups") or []:
            gid = grp.get("id") if isinstance(grp, dict) else grp
            if gid:
                relationships.append(
                    {
                        "source": f"okta:user:{uid}",
                        "target": f"okta:group:{gid}",
                        "relationship": "memberOfGroup",
                    }
                )
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_groups(
    groups: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map Okta group records → ``:Group`` nodes."""
    entities: list[dict[str, Any]] = []
    for group in groups or []:
        gid = group.get("id")
        if not gid:
            continue
        prof = _profile(group)
        entities.append(
            {
                "id": f"okta:group:{gid}",
                "node_type": "Group",
                "name": prof.get("name"),
                "description": prof.get("description"),
                "groupType": group.get("type"),
                "created": group.get("created"),
                "externalToolId": str(gid),
            }
        )
    return ingest_entities(entities, client=client, graph=graph)


def ingest_apps(
    apps: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map Okta application records → ``:Application`` nodes."""
    entities: list[dict[str, Any]] = []
    for app in apps or []:
        aid = app.get("id")
        if not aid:
            continue
        entities.append(
            {
                "id": f"okta:app:{aid}",
                "node_type": "Application",
                "name": app.get("label") or app.get("name"),
                "status": app.get("status"),
                "signOnMode": app.get("signOnMode"),
                "created": app.get("created"),
                "externalToolId": str(aid),
            }
        )
    return ingest_entities(entities, client=client, graph=graph)
