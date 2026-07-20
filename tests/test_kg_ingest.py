"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_users`` / ``ingest_groups`` /
``ingest_apps`` seam with a fake engine client (no engine required), asserting the txn
add_node/commit + edge calls and the Okta record → :User/:Group/:Application mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError

from okta_agent.kg_ingest import (
    ingest_apps,
    ingest_entities,
    ingest_groups,
    ingest_users,
)


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def add_edge(self, txn, source, target, props):
        self.edges.append((source, target, props))

    def commit(self, txn):
        self.committed = True
        return True


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()


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
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "b"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "okta-agent"
    assert c.txn.nodes["a"]["domain"] == "okta"
    assert c.txn.edges == [("a", "b", {"relationship": "memberOfGroup"})]


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
    node = c.txn.nodes["okta:user:00u1"]
    assert node["node_type"] == "User"
    assert node["name"] == "Ada Lovelace"
    assert node["login"] == "ada@acme.com"
    assert node["status"] == "ACTIVE"
    assert node["externalToolId"] == "00u1"
    assert c.txn.edges == [
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
    node = c.txn.nodes["okta:group:00g9"]
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
    node = c.txn.nodes["okta:app:0oa5"]
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
