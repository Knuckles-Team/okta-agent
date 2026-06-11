"""CONCEPT:OKTA-1.1 Applications domain client: templates, assignments, lifecycle."""

import json

import pytest

from okta_agent.api.api_client_apps import build_app_template


def body_of(request) -> dict:
    return json.loads(request.read().decode())


@pytest.mark.concept("OKTA-1.1")
class TestAppTemplates:
    def test_oidc_template_shape(self):
        body = build_app_template(
            "oidc",
            "My OIDC App",
            {"redirect_uris": ["https://app.example.com/cb"]},
        )
        assert body["signOnMode"] == "OPENID_CONNECT"
        assert body["name"] == "oidc_client"
        assert body["settings"]["oauthClient"]["redirect_uris"] == [
            "https://app.example.com/cb"
        ]
        assert body["settings"]["oauthClient"]["grant_types"] == ["authorization_code"]

    def test_saml_template_shape(self):
        body = build_app_template(
            "saml",
            "My SAML App",
            {"sso_acs_url": "https://sp.example.com/acs", "audience": "sp-aud"},
        )
        assert body["signOnMode"] == "SAML_2_0"
        sign_on = body["settings"]["signOn"]
        assert sign_on["ssoAcsUrl"] == "https://sp.example.com/acs"
        assert sign_on["audience"] == "sp-aud"
        assert sign_on["recipient"] == "https://sp.example.com/acs"

    def test_saml_template_requires_acs_and_audience(self):
        with pytest.raises(ValueError, match="sso_acs_url"):
            build_app_template("saml", "x", {"audience": "a"})

    def test_bookmark_template_shape_and_validation(self):
        body = build_app_template(
            "bookmark", "Wiki", {"url": "https://wiki.example.com"}
        )
        assert body["signOnMode"] == "BOOKMARK"
        assert body["settings"]["app"]["url"] == "https://wiki.example.com"
        with pytest.raises(ValueError, match="url"):
            build_app_template("bookmark", "Wiki", {})

    def test_unknown_template_rejected(self):
        with pytest.raises(ValueError, match="Unknown app template"):
            build_app_template("scim", "x", {})


@pytest.mark.concept("OKTA-1.1")
class TestAppsClient:
    def test_create_app_posts_template(self, recorded_api):
        api, recorder = recorded_api
        api.create_app(
            "bookmark", "Wiki", {"url": "https://w.example.com"}, activate=False
        )
        request = recorder.last
        assert request.method == "POST"
        assert request.url.path == "/api/v1/apps"
        assert request.url.params["activate"] == "false"
        assert body_of(request)["label"] == "Wiki"

    def test_update_app_put_full_object(self, recorded_api):
        api, recorder = recorded_api
        api.update_app("a1", {"label": "Renamed"})
        assert recorder.last.method == "PUT"
        assert recorder.last.url.path == "/api/v1/apps/a1"
        assert body_of(recorder.last) == {"label": "Renamed"}

    def test_lifecycle_paths(self, recorded_api):
        api, recorder = recorded_api
        api.activate_app("a1")
        assert recorder.last.url.path == "/api/v1/apps/a1/lifecycle/activate"
        api.deactivate_app("a1")
        assert recorder.last.url.path == "/api/v1/apps/a1/lifecycle/deactivate"

    def test_user_assignment_endpoints(self, recorded_api):
        api, recorder = recorded_api
        api.assign_user_to_app("a1", "u1", profile={"role": "admin"})
        request = recorder.last
        assert request.method == "POST"
        assert request.url.path == "/api/v1/apps/a1/users"
        assert body_of(request) == {
            "id": "u1",
            "scope": "USER",
            "profile": {"role": "admin"},
        }
        api.unassign_user_from_app("a1", "u1")
        assert recorder.last.method == "DELETE"
        assert recorder.last.url.path == "/api/v1/apps/a1/users/u1"

    def test_group_assignment_endpoints(self, recorded_api):
        api, recorder = recorded_api
        api.assign_group_to_app("a1", "g1", priority=2)
        assert recorder.last.method == "PUT"
        assert recorder.last.url.path == "/api/v1/apps/a1/groups/g1"
        assert body_of(recorder.last) == {"priority": 2}
        api.unassign_group_from_app("a1", "g1")
        assert recorder.last.method == "DELETE"
        assert recorder.last.url.path == "/api/v1/apps/a1/groups/g1"
