"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_users`` / ``ingest_groups`` /
``ingest_apps`` seam with a fake engine client (no engine required), asserting the txn
add_node/commit + edge calls and the Okta record → :User/:Group/:Application mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.models.company_brain import ActorType
from agent_utilities.security.brain_context import ActorContext, use_actor

from okta_agent.kg_ingest import (
    ingest_apps,
    ingest_entities,
    ingest_groups,
    ingest_users,
)


@pytest.fixture(autouse=True)
def _governed_session():
    """Bind the authenticated GraphSession required by native ingestion."""
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="__commons__",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "User", "name": "Ada"},
            {"id": "b", "node_type": "Group"},
        ],
        [{"source": "a", "target": "b", "relationship": "memberOfGroup"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.changes.applied
    assert set(c.nodes.values) == {"a", "b"}
    # provenance is stamped
    assert c.nodes.values["a"]["source"] == "okta-agent"
    assert c.nodes.values["a"]["domain"] == "okta"
    assert c.changes.edges == [("a", "b", {"relationship": "memberOfGroup"})]


def test_ingest_users_maps_user_and_group_edge():
    c = _FakeClient()
    res = ingest_users(
        [
            {
                "id": "00u1",
                "status": "ACTIVE",
                "profile": {
                    "firstName": "Ada",
                    "lastName": "Lovelace",
                    "login": "ada@acme.com",
                    "email": "ada@acme.com",
                },
                "groups": [{"id": "00g9"}],
            }
        ],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 1, "edges": 1}
    node = c.nodes.values["okta:user:00u1"]
    assert node["node_type"] == "User"
    assert node["name"] == "Ada Lovelace"
    assert node["login"] == "[REDACTED_EMAIL]"
    assert node["status"] == "ACTIVE"
    assert node["externalToolId"] == "00u1"
    assert c.changes.edges == [
        ("okta:user:00u1", "okta:group:00g9", {"relationship": "memberOfGroup"})
    ]


def test_ingest_groups_maps_group():
    c = _FakeClient()
    res = ingest_groups(
        [
            {
                "id": "00g9",
                "type": "OKTA_GROUP",
                "profile": {"name": "Engineering", "description": "Eng team"},
            }
        ],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 1, "edges": 0}
    node = c.nodes.values["okta:group:00g9"]
    assert node["node_type"] == "Group"
    assert node["name"] == "Engineering"
    assert node["groupType"] == "OKTA_GROUP"
    assert node["externalToolId"] == "00g9"


def test_ingest_apps_maps_application():
    c = _FakeClient()
    res = ingest_apps(
        [
            {
                "id": "0oa5",
                "label": "Salesforce",
                "status": "ACTIVE",
                "signOnMode": "SAML_2_0",
            }
        ],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 1, "edges": 0}
    node = c.nodes.values["okta:app:0oa5"]
    assert node["node_type"] == "Application"
    assert node["name"] == "Salesforce"
    assert node["signOnMode"] == "SAML_2_0"
    assert node["externalToolId"] == "0oa5"


def test_retired_structural_alias_is_rejected():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "a", "type": "User"}], client=_FakeClient())


def test_empty_native_ingest_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
