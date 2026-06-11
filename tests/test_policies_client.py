"""CONCEPT:OKTA-1.1 Policies domain client: type aliases, rules, lifecycle."""

import pytest

from okta_agent.api.api_client_policies import resolve_policy_type


@pytest.mark.concept("OKTA-1.1")
class TestPolicyTypeResolution:
    @pytest.mark.parametrize(
        ("alias", "expected"),
        [
            ("okta_sign_on", "OKTA_SIGN_ON"),
            ("password", "PASSWORD"),
            ("mfa_enroll", "MFA_ENROLL"),
            ("access_policy", "ACCESS_POLICY"),
            ("OKTA_SIGN_ON", "OKTA_SIGN_ON"),
        ],
    )
    def test_aliases_resolve(self, alias, expected):
        assert resolve_policy_type(alias) == expected

    def test_unknown_type_rejected(self):
        with pytest.raises(ValueError, match="Unknown policy type"):
            resolve_policy_type("profile_enrollment_wrong")


@pytest.mark.concept("OKTA-1.1")
class TestPoliciesClient:
    def test_list_policies_params(self, make_api):
        from tests.conftest import RequestRecorder, json_response

        recorder = RequestRecorder(lambda request: json_response([{"id": "p1"}]))
        make_api(recorder).list_policies("password", status="ACTIVE")
        url = recorder.last.url
        assert url.path == "/api/v1/policies"
        assert url.params["type"] == "PASSWORD"
        assert url.params["status"] == "ACTIVE"

    def test_get_policy_with_rules_expand(self, recorded_api):
        api, recorder = recorded_api
        api.get_policy("p1", with_rules=True)
        assert recorder.last.url.path == "/api/v1/policies/p1"
        assert recorder.last.url.params["expand"] == "rules"

    def test_list_policy_rules_path(self, recorded_api):
        api, recorder = recorded_api
        api.list_policy_rules("p1")
        assert recorder.last.url.path == "/api/v1/policies/p1/rules"

    def test_policy_lifecycle_paths(self, recorded_api):
        api, recorder = recorded_api
        api.activate_policy("p1")
        assert recorder.last.url.path == "/api/v1/policies/p1/lifecycle/activate"
        api.deactivate_policy("p1")
        assert recorder.last.url.path == "/api/v1/policies/p1/lifecycle/deactivate"

    def test_rule_lifecycle_paths(self, recorded_api):
        api, recorder = recorded_api
        api.activate_policy_rule("p1", "r1")
        assert recorder.last.url.path == (
            "/api/v1/policies/p1/rules/r1/lifecycle/activate"
        )
        api.deactivate_policy_rule("p1", "r1")
        assert recorder.last.url.path == (
            "/api/v1/policies/p1/rules/r1/lifecycle/deactivate"
        )
