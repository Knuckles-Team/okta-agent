"""CONCEPT:OK-OS.governance.okta System domain client: org, log caps, authenticators, zones."""

import pytest

from okta_agent.api.api_client_system import (
    SYSTEM_LOG_MAX_ITEMS,
    SYSTEM_LOG_PAGE_LIMIT,
)
from tests.conftest import RequestRecorder, json_response, link_next


@pytest.mark.concept("OK-OS.governance.okta")
class TestSystemClient:
    def test_org_path(self, recorded_api):
        api, recorder = recorded_api
        api.get_org()
        assert recorder.last.url.path == "/api/v1/org"

    def test_simple_list_paths(self, recorded_api):
        api, recorder = recorded_api
        api.list_authenticators()
        assert recorder.last.url.path == "/api/v1/authenticators"
        api.list_org_factors()
        assert recorder.last.url.path == "/api/v1/org/factors"

    def test_paginated_list_paths(self, make_api):
        recorder = RequestRecorder(lambda request: json_response([]))
        api = make_api(recorder)
        api.list_authorization_servers()
        assert recorder.last.url.path == "/api/v1/authorizationServers"
        api.list_network_zones()
        assert recorder.last.url.path == "/api/v1/zones"

    def test_system_log_query_params(self, make_api):
        recorder = RequestRecorder(lambda request: json_response([]))
        make_api(recorder).get_system_log(
            since="2026-01-01T00:00:00Z",
            until="2026-01-02T00:00:00Z",
            filter_expr='eventType eq "user.session.start"',
            q="alice",
            sort_order="DESCENDING",
        )
        params = recorder.last.url.params
        assert recorder.last.url.path == "/api/v1/logs"
        assert params["since"] == "2026-01-01T00:00:00Z"
        assert params["until"] == "2026-01-02T00:00:00Z"
        assert params["filter"] == 'eventType eq "user.session.start"'
        assert params["q"] == "alice"
        assert params["sortOrder"] == "DESCENDING"
        assert params["limit"] == "100"

    def test_system_log_page_limit_clamped(self, make_api):
        recorder = RequestRecorder(lambda request: json_response([]))
        make_api(recorder).get_system_log(limit=999999)
        assert recorder.last.url.params["limit"] == str(SYSTEM_LOG_PAGE_LIMIT)

    def test_system_log_overall_cap_enforced(self, make_api):
        page = [{"uuid": str(i)} for i in range(600)]

        def handler(request):
            return json_response(page, headers=link_next("more", path="/api/v1/logs"))

        result = make_api(handler).get_system_log(max_items=10_000_000)
        assert result["count"] == SYSTEM_LOG_MAX_ITEMS
        assert result["truncated"] is True
        assert result["next_cursor"] == "more"
