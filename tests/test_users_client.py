"""CONCEPT:OKTA-1.1 Users domain client: paths, params, and body shapes."""

import json

import pytest


def body_of(request) -> dict:
    return json.loads(request.read().decode())


@pytest.mark.concept("OKTA-1.1")
class TestUsersClient:
    def test_list_users_params(self, recorded_api):
        api, recorder = recorded_api
        api.list_users(q="alice", filter_expr='status eq "ACTIVE"', limit=50)
        url = recorder.last.url
        assert url.path == "/api/v1/users"
        assert url.params["q"] == "alice"
        assert url.params["filter"] == 'status eq "ACTIVE"'
        assert url.params["limit"] == "50"

    def test_list_users_page_limit_capped_at_200(self, recorded_api):
        api, recorder = recorded_api
        api.list_users(limit=5000)
        assert recorder.last.url.params["limit"] == "200"

    def test_search_users_builds_scim_filter(self, recorded_api):
        api, recorder = recorded_api
        api.search_users(
            conditions=[{"field": "profile.department", "op": "eq", "value": "Eng"}]
        )
        assert recorder.last.url.params["filter"] == 'profile.department eq "Eng"'

    def test_get_user_path(self, recorded_api):
        api, recorder = recorded_api
        api.get_user("alice@example.com")
        assert recorder.last.url.path == "/api/v1/users/alice@example.com"
        assert recorder.last.method == "GET"

    def test_create_user_activate_flag_and_body(self, recorded_api):
        api, recorder = recorded_api
        profile = {
            "firstName": "Ada",
            "lastName": "Lovelace",
            "email": "ada@example.com",
            "login": "ada@example.com",
        }
        api.create_user(profile, group_ids=["g1"], activate=False)
        request = recorder.last
        assert request.method == "POST"
        assert request.url.path == "/api/v1/users"
        assert request.url.params["activate"] == "false"
        body = body_of(request)
        assert body["profile"] == profile
        assert body["groupIds"] == ["g1"]
        assert "credentials" not in body

    def test_update_user_partial_post(self, recorded_api):
        api, recorder = recorded_api
        api.update_user("u1", profile={"nickName": "ada"})
        request = recorder.last
        assert request.method == "POST"
        assert request.url.path == "/api/v1/users/u1"
        assert body_of(request) == {"profile": {"nickName": "ada"}}

    @pytest.mark.parametrize(
        ("method_name", "suffix"),
        [
            ("suspend_user", "suspend"),
            ("unsuspend_user", "unsuspend"),
            ("unlock_user", "unlock"),
        ],
    )
    def test_simple_lifecycle_endpoints(self, recorded_api, method_name, suffix):
        api, recorder = recorded_api
        getattr(api, method_name)("u1")
        assert recorder.last.method == "POST"
        assert recorder.last.url.path == f"/api/v1/users/u1/lifecycle/{suffix}"

    def test_activate_and_deactivate_send_email_param(self, recorded_api):
        api, recorder = recorded_api
        api.activate_user("u1", send_email=True)
        assert recorder.last.url.path == "/api/v1/users/u1/lifecycle/activate"
        assert recorder.last.url.params["sendEmail"] == "true"
        api.deactivate_user("u1")
        assert recorder.last.url.path == "/api/v1/users/u1/lifecycle/deactivate"
        assert recorder.last.url.params["sendEmail"] == "false"

    def test_expire_password_variants(self, recorded_api):
        api, recorder = recorded_api
        api.expire_password("u1")
        assert recorder.last.url.path == "/api/v1/users/u1/lifecycle/expire_password"
        api.expire_password("u1", temp_password=True)
        assert recorder.last.url.path == (
            "/api/v1/users/u1/lifecycle/expire_password_with_temp_password"
        )

    def test_reset_password_send_email_option(self, recorded_api):
        api, recorder = recorded_api
        api.reset_password("u1", send_email=False)
        assert recorder.last.url.path == "/api/v1/users/u1/lifecycle/reset_password"
        assert recorder.last.url.params["sendEmail"] == "false"

    def test_related_resource_paths(self, recorded_api):
        api, recorder = recorded_api
        api.list_user_apps("u1")
        assert recorder.last.url.path == "/api/v1/users/u1/appLinks"
        api.list_user_factors("u1")
        assert recorder.last.url.path == "/api/v1/users/u1/factors"

    def test_list_user_groups_paginated_path(self, make_api):
        from tests.conftest import RequestRecorder, json_response

        recorder = RequestRecorder(lambda request: json_response([{"id": "g1"}]))
        api = make_api(recorder)
        result = api.list_user_groups("u1")
        assert recorder.last.url.path == "/api/v1/users/u1/groups"
        assert result["count"] == 1

    def test_clear_sessions_oauth_tokens_option(self, recorded_api):
        api, recorder = recorded_api
        api.clear_user_sessions("u1", oauth_tokens=True)
        assert recorder.last.method == "DELETE"
        assert recorder.last.url.path == "/api/v1/users/u1/sessions"
        assert recorder.last.url.params["oauthTokens"] == "true"
