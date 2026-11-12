"""CONCEPT:OK-OS.identity.default Destructive operations use the SDK's one declaration and guard."""

import asyncio
from unittest.mock import patch

import httpx
import pytest
from fastmcp import Client
from scion_sdk.connector import build_server

from tests.conftest import RequestRecorder, json_response

DESTRUCTIVE_TOOLS = {
    "okta_deactivate_user": {"user_id": "u1"},
    "okta_suspend_user": {"user_id": "u1"},
    "okta_expire_password": {"user_id": "u1"},
    "okta_reset_password": {"user_id": "u1"},
    "okta_clear_user_sessions": {"user_id": "u1"},
    "okta_delete_group": {"group_id": "g1"},
    "okta_remove_group_member": {"group_id": "g1", "user_id": "u1"},
    "okta_deactivate_group_rule": {"rule_id": "r1"},
    "okta_deactivate_app": {"app_id": "a1"},
    "okta_unassign_user_from_app": {"app_id": "a1", "user_id": "u1"},
    "okta_unassign_group_from_app": {"app_id": "a1", "group_id": "g1"},
    "okta_deactivate_policy": {"policy_id": "p1"},
    "okta_deactivate_policy_rule": {"policy_id": "p1", "rule_id": "r1"},
}


def _server(recorder: RequestRecorder, monkeypatch):
    real = httpx.Client

    def client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(recorder)
        return real(*args, **kwargs)

    monkeypatch.setattr("okta_agent.api.api_client_base.httpx.Client", client)
    monkeypatch.setenv("OKTA_ORG_URL", "https://example.okta.com")
    monkeypatch.setenv("OKTA_API_TOKEN", "x")
    with patch("sys.argv", ["okta-mcp"]):
        return build_server("okta_agent", command_args=[])[1]


@pytest.mark.concept("OK-OS.identity.default")
@pytest.mark.spec("CONN-OKTA-AGENT-CONNECTOR-CONTENT-R002")
def test_declared_operations_are_destructive_tools_that_ask_first(monkeypatch):
    monkeypatch.delenv("SCION_ALLOW_DESTRUCTIVE", raising=False)
    recorder = RequestRecorder(lambda request: json_response({}))
    mcp = _server(recorder, monkeypatch)

    async def _run():
        async with Client(mcp) as client:
            tools = {t.name: t for t in await client.list_tools()}
            for name in DESTRUCTIVE_TOOLS:
                tool = tools[name]
                assert tool.annotations.destructive_hint is True, name
                properties = tool.input_schema["properties"]
                assert "confirm" in properties and "allow_destructive" not in properties
            assert tools["okta_get_user"].annotations.destructive_hint is False
            return client

    asyncio.run(_run())


@pytest.mark.concept("OK-OS.identity.default")
@pytest.mark.spec("CONN-OKTA-AGENT-CONNECTOR-CONTENT-R002")
@pytest.mark.parametrize("name", sorted(DESTRUCTIVE_TOOLS))
def test_unconfirmed_call_sends_no_request_and_confirmed_call_sends_one(
    name, monkeypatch
):
    monkeypatch.delenv("SCION_ALLOW_DESTRUCTIVE", raising=False)
    recorder = RequestRecorder(lambda request: json_response({}))
    mcp = _server(recorder, monkeypatch)
    arguments = DESTRUCTIVE_TOOLS[name]

    async def _run():
        async with Client(mcp) as client:
            refused = await client.call_tool(name, arguments)
            assert refused.structured_content["cancelled"] is True
            assert recorder.requests == []
            await client.call_tool(name, {**arguments, "confirm": True})

    asyncio.run(_run())
    assert len(recorder.requests) == 1
