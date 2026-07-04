"""Native epistemic-graph ingestion for Okta records (typed graph nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The okta-agent connector natively
pushes its Okta Management API data into the ONE epistemic-graph knowledge graph as
**typed OWL nodes** (``:User``, ``:Group``, ``:Application``, …) + links, using the
lightweight engine client (``GraphComputeEngine()._client`` + ``txn``) — the same fast
client the blob ``MediaStore`` uses, NOT the heavy in-process ingestion engine.

Entirely best-effort and dependency-/engine-guarded: with no agent-utilities KG stack or
no reachable engine every entry point **no-ops** (returns ``None``), so the connector keeps
working with zero KG infrastructure. Nodes carry the shared provenance (``domain``/``source``)
and use ids ``okta:<class>:<extId>``; each ``type`` matches a class the ``okta_agent.ontology``
``okta.ttl`` federates.

Prefers the shared ``agent_utilities.knowledge_graph.memory.native_ingest`` primitive when it
is importable; otherwise falls back to a self-contained txn write against the same fast client
(the primitive is not yet in the installed agent_utilities).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("okta_agent.kg")

_SOURCE = "okta-agent"
_DOMAIN = "okta"


# --------------------------------------------------------------------------- #
# Engine plumbing (guarded — shared primitive first, self-contained fallback)
# --------------------------------------------------------------------------- #
def _client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` when unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or "__commons__")
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed nodes (+ edges) into epistemic-graph via the fast engine client.

    ``entities``: ``[{"id":..., "type":<owl:Class>, ...props}]``.
    ``relationships``: ``[{"source":id, "target":id, "type":rel}]``.
    Returns ``{"nodes":n, "edges":m}`` or ``None`` (no engine / failure; never raises).
    ``client``/``graph`` may be injected (tests); otherwise resolved on demand.
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None

    # Prefer the shared primitive when present (single txn-write implementation).
    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_entities as _shared,
            )

            return _shared(
                entities, relationships, source=source, domain=domain, graph=graph
            )
        except Exception as e:  # noqa: BLE001 — primitive absent; use fallback
            logger.debug("KG ingest: shared primitive unavailable: %s", e)

    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _write_nodes(
        client, graph or "__commons__", entities, relationships, source, domain
    )


def _write_nodes(
    client: Any,
    graph: str,
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
    source: str,
    domain: str,
) -> dict[str, int] | None:
    """Self-contained txn fallback: stamp provenance, MERGE nodes, add edges."""
    try:
        txn = client.txn.begin(graph=graph)
        for node in nodes:
            props = {k: v for k, v in node.items() if k != "id" and v is not None}
            props.setdefault("source", source)
            props.setdefault("domain", domain)
            client.txn.add_node(txn, node["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest: wrote %d nodes, %d edges", len(nodes), edges)
    return {"nodes": len(nodes), "edges": edges}


# --------------------------------------------------------------------------- #
# Record → typed-node mappers
# --------------------------------------------------------------------------- #
def _profile(rec: dict[str, Any]) -> dict[str, Any]:
    prof = rec.get("profile")
    return prof if isinstance(prof, dict) else {}


def ingest_users(
    users: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
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
                "type": "User",
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
                        "type": "memberOfGroup",
                    }
                )
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_groups(
    groups: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
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
                "type": "Group",
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
) -> dict[str, int] | None:
    """Map Okta application records → ``:Application`` nodes."""
    entities: list[dict[str, Any]] = []
    for app in apps or []:
        aid = app.get("id")
        if not aid:
            continue
        entities.append(
            {
                "id": f"okta:app:{aid}",
                "type": "Application",
                "name": app.get("label") or app.get("name"),
                "status": app.get("status"),
                "signOnMode": app.get("signOnMode"),
                "created": app.get("created"),
                "externalToolId": str(aid),
            }
        )
    return ingest_entities(entities, client=client, graph=graph)
