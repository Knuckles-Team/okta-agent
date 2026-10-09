"""Epistemic-graph typed-node ingestion -- Wire-First coverage for okta-agent.

Exercises the real ``ingest_entities`` / ``ingest_users`` / ``ingest_groups`` /
``ingest_apps`` seam against a fake ``agent_connector_sdk.ingest`` transport (no engine
required). The real SDK request builder (``agent_connector_sdk.ingest.request
.build_request``) still runs, so a malformed change set is still caught by the SDK's own
contract, not re-derived here; only the final network commit is faked.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest
from epistemic_graph.generated.source_ingestion import SourceIngestionRequest

from okta_agent.kg_ingest import (
    ingest_apps,
    ingest_entities,
    ingest_groups,
    ingest_users,
)


class _FakeTransport:
    """Records every submitted request; no epistemic-graph engine required."""

    def __init__(self) -> None:
        self.requests: list[SourceIngestionRequest] = []

    async def source_status(self, _connector: str, _stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: SourceIngestionRequest) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, _data: bytes) -> str:
        raise AssertionError("okta-agent identity ingestion carries no media")


@pytest.fixture
def ingest() -> tuple[KnowledgeIngest, _FakeTransport]:
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


@pytest.mark.asyncio
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
        [
            {"id": "a", "node_type": "User", "name": "Ada"},
            {"id": "b", "node_type": "Group"},
        ],
        [{"source": "a", "target": "b", "relationship": "memberOfGroup"}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(transport.requests) == 1
    request = transport.requests[0]
    record_ids = {record.record_id for record in request.records}
    assert record_ids == {"a", "b"}
    a_record = next(r for r in request.records if r.record_id == "a")
    assert a_record.payload["name"] == "Ada"
    assert request.relationships[0].relation_reference.endswith(
        "resources/User/relations/memberOfGroup"
    )


@pytest.mark.asyncio
async def test_ingest_users_maps_user_and_group_edge(ingest):
    service, transport = ingest
    res = await ingest_users(
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
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 1}
    request = transport.requests[0]
    node = next(r for r in request.records if r.record_id == "okta:user:00u1")
    assert node.payload["name"] == "Ada Lovelace"
    # the SDK's PersistencePrivacyGuard (IngestBinding.sanitize, default True)
    # redacts email-shaped text in any non-structural property.
    assert node.payload["login"] == "[REDACTED_EMAIL]"
    assert node.payload["status"] == "ACTIVE"
    assert node.payload["externalToolId"] == "00u1"
    assert request.relationships[0].relation_reference.endswith(
        "resources/User/relations/memberOfGroup"
    )


@pytest.mark.asyncio
async def test_ingest_groups_maps_group(ingest):
    service, transport = ingest
    res = await ingest_groups(
        [
            {
                "id": "00g9",
                "type": "OKTA_GROUP",
                "profile": {"name": "Engineering", "description": "Eng team"},
            }
        ],
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 0}
    request = transport.requests[0]
    node = next(r for r in request.records if r.record_id == "okta:group:00g9")
    assert node.payload["name"] == "Engineering"
    assert node.payload["groupType"] == "OKTA_GROUP"
    assert node.payload["externalToolId"] == "00g9"


@pytest.mark.asyncio
async def test_ingest_apps_maps_application(ingest):
    service, transport = ingest
    res = await ingest_apps(
        [
            {
                "id": "0oa5",
                "label": "Salesforce",
                "status": "ACTIVE",
                "signOnMode": "SAML_2_0",
            }
        ],
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 0}
    request = transport.requests[0]
    node = next(r for r in request.records if r.record_id == "okta:app:0oa5")
    assert node.payload["name"] == "Salesforce"
    assert node.payload["signOnMode"] == "SAML_2_0"
    assert node.payload["externalToolId"] == "0oa5"


@pytest.mark.asyncio
async def test_retired_structural_alias_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="node_type"):
        await ingest_entities([{"id": "a", "type": "User"}], ingest=service)


@pytest.mark.asyncio
async def test_empty_native_ingest_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
