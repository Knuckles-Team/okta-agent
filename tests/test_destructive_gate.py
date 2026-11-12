"""CONCEPT:OK-OS.identity.default Destructive operations are gated on the client and served as typed tools."""

import asyncio
from unittest.mock import patch

import pytest
from fastmcp import Client
from scion_sdk.connector import build_server

from okta_agent.api.api_client_base import DestructiveBlockedError
from tests.conftest import RequestRecorder, json_response

DESTRUCTIVE_CALLS = [
    ("deactivate_user", ("u1",)),
    ("suspend_user", ("u1",)),
    ("expire_password", ("u1",)),
    ("reset_password", ("u1",)),
    ("clear_user_sessions", ("u1",)),
    ("delete_group", ("g1",)),
    ("remove_group_member", ("g1", "u1")),
    ("deactivate_group_rule", ("r1",)),
    ("deactivate_app", ("a1",)),
    ("unassign_user_from_app", ("a1", "u1")),
    ("unassign_group_from_app", ("a1", "g1")),
    ("deactivate_policy", ("p1",)),
    ("deactivate_policy_rule", ("p1", "r1")),
]


@pytest.mark.concept("OK-OS.identity.default")
@pytest.mark.parametrize(("method", "args"), DESTRUCTIVE_CALLS)
def test_destructive_operation_is_blocked_by_default(make_api, method, args):
    recorder = RequestRecorder(lambda request: json_response({}))
    api = make_api(recorder)
    with pytest.raises(DestructiveBlockedError, match="allow_destructive"):
        getattr(api, method)(*args)
    assert recorder.requests == []


@pytest.mark.concept("OK-OS.identity.default")
@pytest.mark.parametrize(("method", "args"), DESTRUCTIVE_CALLS)
def test_per_call_flag_allows_the_operation(make_api, method, args):
    recorder = RequestRecorder(lambda request: json_response({}))
    api = make_api(recorder)
    getattr(api, method)(*args, allow_destructive=True)
    assert len(recorder.requests) == 1


@pytest.mark.concept("OK-OS.identity.default")
def test_environment_default_allows_the_operation(make_api, monkeypatch):
    monkeypatch.setenv("OKTA_ALLOW_DESTRUCTIVE", "True")
    recorder = RequestRecorder(lambda request: json_response({}))
    make_api(recorder).deactivate_user("u1")
    assert len(recorder.requests) == 1


@pytest.mark.concept("OK-OS.identity.default")
def test_non_destructive_operation_needs_no_flag(make_api):
    recorder = RequestRecorder(lambda request: json_response({"id": "u1"}))
    make_api(recorder).get_user("u1")
    assert len(recorder.requests) == 1


@pytest.mark.concept("OK-OS.governance.okta-2")
def test_served_surface_is_typed_and_names_the_gate():
    with (
        patch.dict(
            "os.environ",
            {"OKTA_ORG_URL": "https://example.okta.com", "OKTA_API_TOKEN": "x"},
        ),
        patch("sys.argv", ["okta-mcp"]),
    ):
        mcp = build_server("okta_agent", command_args=[])[1]

    async def _list():
        async with Client(mcp) as client:
            return await client.list_tools()

    tools = {t.name: t for t in asyncio.run(_list())}
    assert "okta_deactivate_user" in tools
    assert (
        "allow_destructive" in tools["okta_deactivate_user"].inputSchema["properties"]
    )
    assert not {
        "okta_users",
        "okta_groups",
        "okta_apps",
        "okta_policies",
        "okta_system",
    } & set(tools)
    for tool in tools.values():
        assert "action" not in (tool.inputSchema.get("properties") or {})
