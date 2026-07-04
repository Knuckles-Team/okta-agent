"""CONCEPT:OK-OS.governance.okta-2 / CONCEPT:OK-OS.identity.default Action routing and destructive gating."""

import httpx
import pytest
from fastmcp import Client, FastMCP

import okta_agent.mcp.mcp_apps as mcp_apps
import okta_agent.mcp.mcp_groups as mcp_groups
import okta_agent.mcp.mcp_policies as mcp_policies
import okta_agent.mcp.mcp_system as mcp_system
import okta_agent.mcp.mcp_users as mcp_users
from okta_agent.api.credentials import SswsToken
from okta_agent.api_client import Api
from tests.conftest import ORG_URL, TEST_TOKEN, RequestRecorder, json_response


@pytest.fixture
def mock_client(monkeypatch):
    """Patch every tool module's get_client to a mocked Api; return its recorder."""
    recorder = RequestRecorder(lambda request: json_response({"id": "x"}))
    api = Api(
        org_url=ORG_URL,
        credential=SswsToken(TEST_TOKEN),
        transport=httpx.MockTransport(recorder),
    )
    for module in (mcp_users, mcp_groups, mcp_apps, mcp_policies, mcp_system):
        monkeypatch.setattr(module, "get_client", lambda: api)
    return recorder


@pytest.mark.concept("OK-OS.identity.default")
class TestDestructiveGating:
    async def test_destructive_blocked_by_default(self, mock_client):
        result = await mcp_users.run_users("deactivate", '{"user_id": "u1"}')
        assert "allow_destructive" in result["error"]["message"]
        assert mock_client.requests == []

    async def test_destructive_allowed_with_per_call_flag(self, mock_client):
        result = await mcp_users.run_users(
            "deactivate", '{"user_id": "u1"}', allow_destructive=True
        )
        assert "error" not in result
        assert mock_client.last.url.path == "/api/v1/users/u1/lifecycle/deactivate"

    async def test_destructive_allowed_via_env_default(self, mock_client, monkeypatch):
        monkeypatch.setenv("OKTA_ALLOW_DESTRUCTIVE", "True")
        result = await mcp_users.run_users("clear_sessions", '{"user_id": "u1"}')
        assert "error" not in result
        assert mock_client.last.method == "DELETE"

    @pytest.mark.parametrize(
        ("runner", "action", "params"),
        [
            (mcp_users.run_users, "suspend", '{"user_id": "u1"}'),
            (mcp_users.run_users, "reset_password", '{"user_id": "u1"}'),
            (mcp_users.run_users, "expire_password", '{"user_id": "u1"}'),
            (mcp_groups.run_groups, "delete", '{"group_id": "g1"}'),
            (
                mcp_groups.run_groups,
                "remove_member",
                '{"group_id": "g1", "user_id": "u1"}',
            ),
            (mcp_groups.run_groups, "deactivate_rule", '{"rule_id": "r1"}'),
            (mcp_apps.run_apps, "deactivate", '{"app_id": "a1"}'),
            (mcp_apps.run_apps, "unassign_user", '{"app_id": "a1", "user_id": "u1"}'),
            (mcp_apps.run_apps, "unassign_group", '{"app_id": "a1", "group_id": "g1"}'),
            (mcp_policies.run_policies, "deactivate", '{"policy_id": "p1"}'),
            (
                mcp_policies.run_policies,
                "deactivate_rule",
                '{"policy_id": "p1", "rule_id": "r1"}',
            ),
        ],
    )
    async def test_all_destructive_actions_gated(
        self, mock_client, runner, action, params
    ):
        result = await runner(action, params)
        assert "allow_destructive" in result["error"]["message"]
        assert mock_client.requests == []

    async def test_non_destructive_actions_pass_without_flag(self, mock_client):
        result = await mcp_users.run_users("unlock", '{"user_id": "u1"}')
        assert "error" not in result
        result = await mcp_users.run_users("unsuspend", '{"user_id": "u1"}')
        assert "error" not in result


@pytest.mark.concept("OK-OS.governance.okta-2")
class TestActionRouting:
    async def test_users_list_routes(self, mock_client):
        def list_handler(request):
            return json_response([{"id": "u1"}])

        mock_client._responder = list_handler
        result = await mcp_users.run_users("list", '{"q": "alice"}')
        assert result["count"] == 1
        assert mock_client.last.url.params["q"] == "alice"

    async def test_unknown_action_envelope(self, mock_client):
        result = await mcp_users.run_users("explode")
        assert "Unknown users action" in result["error"]["message"]
        result = await mcp_system.run_system("explode")
        assert "Unknown system action" in result["error"]["message"]

    async def test_invalid_params_json_envelope(self, mock_client):
        result = await mcp_users.run_users("list", "{not json")
        assert "Invalid params_json" in result["error"]["message"]

    async def test_non_object_params_json_envelope(self, mock_client):
        result = await mcp_groups.run_groups("list", "[1, 2]")
        assert "Invalid params_json" in result["error"]["message"]

    async def test_missing_required_param_envelope(self, mock_client):
        result = await mcp_users.run_users("get", "{}")
        assert "Missing required parameter" in result["error"]["message"]
        assert mock_client.requests == []

    async def test_okta_error_maps_to_envelope(self, monkeypatch):
        def handler(request):
            return json_response(
                {"errorCode": "E0000006", "errorSummary": "Access denied"},
                status=403,
            )

        api = Api(
            org_url=ORG_URL,
            credential=SswsToken(TEST_TOKEN),
            transport=httpx.MockTransport(handler),
        )
        monkeypatch.setattr(mcp_users, "get_client", lambda: api)
        result = await mcp_users.run_users("get", '{"user_id": "u1"}')
        assert result["error"]["status"] == 403
        assert result["error"]["error_code"] == "E0000006"

    async def test_policies_writes_out_of_scope(self, mock_client):
        for action in ("create", "update", "create_rule", "delete"):
            result = await mcp_policies.run_policies(action, "{}")
            assert "out of scope" in result["error"]["message"]
        assert mock_client.requests == []

    async def test_system_logs_routes_with_caps(self, mock_client):
        def log_handler(request):
            return json_response([])

        mock_client._responder = log_handler
        result = await mcp_system.run_system(
            "logs", '{"since": "2026-01-01T00:00:00Z", "limit": 50000}'
        )
        assert "error" not in result
        assert mock_client.last.url.params["limit"] == "1000"


@pytest.mark.concept("OK-OS.governance.okta-2")
class TestToolRegistration:
    async def test_all_five_tools_register(self):
        from okta_agent.mcp import (
            register_apps_tools,
            register_groups_tools,
            register_policies_tools,
            register_system_tools,
            register_users_tools,
        )

        mcp = FastMCP("okta-test")
        register_users_tools(mcp)
        register_groups_tools(mcp)
        register_apps_tools(mcp)
        register_policies_tools(mcp)
        register_system_tools(mcp)
        names = {tool.name for tool in await mcp.list_tools()}
        assert names == {
            "okta_users",
            "okta_groups",
            "okta_apps",
            "okta_policies",
            "okta_system",
        }

    async def test_call_through_fastmcp_client(self, mock_client):
        from okta_agent.mcp import register_system_tools

        mcp = FastMCP("okta-test")
        register_system_tools(mcp)
        async with Client(mcp) as client:
            result = await client.call_tool("okta_system", {"action": "org"})
        assert result.data["data"]["id"] == "x"
        assert result.data["rate_limit"]["remaining"] == 599

    async def test_destructive_gate_through_fastmcp_client(self, mock_client):
        from okta_agent.mcp import register_users_tools

        mcp = FastMCP("okta-test")
        register_users_tools(mcp)
        async with Client(mcp) as client:
            result = await client.call_tool(
                "okta_users",
                {"action": "deactivate", "params_json": '{"user_id": "u1"}'},
            )
        assert "allow_destructive" in result.data["error"]["message"]
        assert mock_client.requests == []
