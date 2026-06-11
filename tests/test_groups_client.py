"""CONCEPT:OKTA-1.1 Groups domain client: paths, params, and body shapes."""

import json

import pytest


def body_of(request) -> dict:
    return json.loads(request.read().decode())


@pytest.mark.concept("OKTA-1.1")
class TestGroupsClient:
    def test_list_groups_params(self, recorded_api):
        api, recorder = recorded_api
        api.list_groups(q="eng", limit=10)
        assert recorder.last.url.path == "/api/v1/groups"
        assert recorder.last.url.params["q"] == "eng"

    def test_search_groups_builds_filter(self, recorded_api):
        api, recorder = recorded_api
        api.search_groups(
            conditions=[{"field": "type", "op": "eq", "value": "OKTA_GROUP"}]
        )
        assert recorder.last.url.params["filter"] == 'type eq "OKTA_GROUP"'

    def test_create_group_body(self, recorded_api):
        api, recorder = recorded_api
        api.create_group("Engineering", description="Eng org")
        request = recorder.last
        assert request.method == "POST"
        assert request.url.path == "/api/v1/groups"
        assert body_of(request) == {
            "profile": {"name": "Engineering", "description": "Eng org"}
        }

    def test_update_group_put(self, recorded_api):
        api, recorder = recorded_api
        api.update_group("g1", "Engineering")
        request = recorder.last
        assert request.method == "PUT"
        assert request.url.path == "/api/v1/groups/g1"
        assert body_of(request) == {"profile": {"name": "Engineering"}}

    def test_delete_group(self, recorded_api):
        api, recorder = recorded_api
        api.delete_group("g1")
        assert recorder.last.method == "DELETE"
        assert recorder.last.url.path == "/api/v1/groups/g1"

    def test_membership_endpoints(self, recorded_api):
        api, recorder = recorded_api
        api.add_group_member("g1", "u1")
        assert recorder.last.method == "PUT"
        assert recorder.last.url.path == "/api/v1/groups/g1/users/u1"
        api.remove_group_member("g1", "u1")
        assert recorder.last.method == "DELETE"
        assert recorder.last.url.path == "/api/v1/groups/g1/users/u1"

    def test_list_members_paginated_path(self, make_api):
        from tests.conftest import RequestRecorder, json_response

        recorder = RequestRecorder(lambda request: json_response([{"id": "u1"}]))
        make_api(recorder).list_group_members("g1")
        assert recorder.last.url.path == "/api/v1/groups/g1/users"

    def test_create_group_rule_body_shape(self, recorded_api):
        api, recorder = recorded_api
        api.create_group_rule(
            "eng-rule", 'user.department=="Engineering"', ["g1", "g2"]
        )
        body = body_of(recorder.last)
        assert recorder.last.url.path == "/api/v1/groups/rules"
        assert body["type"] == "group_rule"
        assert body["conditions"]["expression"] == {
            "type": "urn:okta:expression:1.0",
            "value": 'user.department=="Engineering"',
        }
        assert body["actions"]["assignUserToGroups"]["groupIds"] == ["g1", "g2"]

    def test_group_rule_lifecycle_paths(self, recorded_api):
        api, recorder = recorded_api
        api.activate_group_rule("r1")
        assert recorder.last.url.path == "/api/v1/groups/rules/r1/lifecycle/activate"
        api.deactivate_group_rule("r1")
        assert recorder.last.url.path == "/api/v1/groups/rules/r1/lifecycle/deactivate"
