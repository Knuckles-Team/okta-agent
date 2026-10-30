"""Epistemic-graph ingestion for Okta identity records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. Nodes use canonical ``node_type``
and edges use canonical ``relationship``, pushed into the ONE epistemic-graph
knowledge graph through ``scion_sdk.ingest`` -- the generated ``SourceIngest``
client, not a local ingestion helper.
"""

from __future__ import annotations

import logging
from typing import Any

from scion_sdk.ingest import (
    KnowledgeIngest,
    SourceStream,
)

logger = logging.getLogger("okta_agent.kg")

STREAM = SourceStream.for_package(__package__.split(".")[0], "okta")


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


async def ingest_users(
    users: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
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
    return await STREAM.entities(entities, relationships, ingest=ingest)


async def ingest_groups(
    groups: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
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
    return await STREAM.entities(entities, ingest=ingest)


async def ingest_apps(
    apps: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
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
    return await STREAM.entities(entities, ingest=ingest)
