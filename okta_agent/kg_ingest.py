"""Native epistemic-graph ingestion for Okta identity records.

All writes use the required ``agent_utilities.knowledge_graph.memory.native_ingest``
primitive. Nodes use canonical ``node_type`` and edges use canonical ``relationship``;
nodes and edges commit in one native transaction. Missing engine dependencies, rejected
records, conflicts, and transaction failures propagate as ``NativeIngestError``.
"""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("okta_agent.kg")

_SOURCE = "okta-agent"
_DOMAIN = "okta"


def ingest_entities(*args: object, **kwargs: object) -> object:
    """Write canonical typed nodes and relationships in one native transaction.

    SDK-GAP: Always raises now; see KnowledgeGraphIngestUnavailable.
    """
    _kg_unavailable("ingest_entities")


def _profile(rec: dict[str, Any]) -> dict[str, Any]:
    prof = rec.get("profile")
    return prof if isinstance(prof, dict) else {}


def _user_entity(uid: str, user: dict[str, Any]) -> dict[str, Any]:
    prof = _profile(user)
    return {
        "id": f"okta:user:{uid}",
        "node_type": "User",
        "name": " ".join(p for p in (prof.get("firstName"), prof.get("lastName")) if p)
        or prof.get("login"),
        "login": prof.get("login"),
        "email": prof.get("email"),
        "status": user.get("status"),
        "created": user.get("created"),
        "lastLogin": user.get("lastLogin"),
        "externalToolId": str(uid),
    }


def _user_group_relationships(uid: str, user: dict[str, Any]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
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
    return relationships


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
        entities.append(_user_entity(uid, user))
        relationships.extend(_user_group_relationships(uid, user))
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


class KnowledgeGraphIngestUnavailable(RuntimeError):
    """Direct-to-graph ingestion is unavailable from this connector.

    SDK-GAP (EH-48x, /var/tmp/l9/finish/au-decon-G4c/SDK-GAPS.md): raised in
    place of the old ``agent_utilities.knowledge_graph`` native-ingest call --
    agent-connector-sdk has no facade over EG's typed ingestion protocol yet,
    and the fleet precedent (agents/world-reference-mcp) moves direct-to-graph
    delivery to agent_connector_sdk.runner/sinks at the deployment layer, out
    of connector scope.
    """


def _kg_unavailable(name: str) -> None:
    raise KnowledgeGraphIngestUnavailable(
        f"{name}: direct-to-graph ingestion moved out of connector code "
        "(agent-utilities removed); no agent-connector-sdk facade exists yet "
        "-- see SDK-GAPS.md"
    )
