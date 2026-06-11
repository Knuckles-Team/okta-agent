"""CONCEPT:OKTA-1.1 Okta Applications API client (apps, assignments, lifecycle).

Mirrors the keycloak-agent clients verb taxonomy (list/get/create/update,
activate/deactivate — Keycloak "clients" are Okta "apps") so agents can switch
IdPs with familiar verbs. ``create_app`` ships three basic templates: ``oidc``,
``saml`` and ``bookmark``.

API reference:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Application/
"""

from typing import Any

from okta_agent.api.api_client_base import ApiClientBase, drop_none

APPS_PAGE_LIMIT = 200
APP_TEMPLATES = ("oidc", "saml", "bookmark")


def build_app_template(
    template: str, label: str, settings: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build a create-app request body from a basic template.

    Templates:

    - ``oidc`` — an OPENID_CONNECT web app; ``settings`` may carry
      ``redirect_uris`` (list), ``grant_types``, ``response_types``,
      ``application_type`` and ``token_endpoint_auth_method``.
    - ``saml`` — a SAML_2_0 app; ``settings`` must carry ``sso_acs_url`` and
      ``audience``.
    - ``bookmark`` — a bookmark tile; ``settings`` must carry ``url``.

    Body shapes per
    https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Application/#tag/Application/operation/createApplication
    """
    settings = settings or {}
    if template == "oidc":
        oauth_client = {
            "redirect_uris": settings.get("redirect_uris", []),
            "response_types": settings.get("response_types", ["code"]),
            "grant_types": settings.get("grant_types", ["authorization_code"]),
            "application_type": settings.get("application_type", "web"),
        }
        return {
            "name": "oidc_client",
            "label": label,
            "signOnMode": "OPENID_CONNECT",
            "credentials": {
                "oauthClient": {
                    "token_endpoint_auth_method": settings.get(
                        "token_endpoint_auth_method", "client_secret_basic"
                    )
                }
            },
            "settings": {"oauthClient": oauth_client},
        }
    if template == "saml":
        for required in ("sso_acs_url", "audience"):
            if required not in settings:
                raise ValueError(f"SAML template requires settings[{required!r}].")
        sign_on = {
            "ssoAcsUrl": settings["sso_acs_url"],
            "audience": settings["audience"],
            "recipient": settings.get("recipient", settings["sso_acs_url"]),
            "destination": settings.get("destination", settings["sso_acs_url"]),
            "subjectNameIdTemplate": settings.get(
                "subject_name_id_template", "${user.userName}"
            ),
            "subjectNameIdFormat": settings.get(
                "subject_name_id_format",
                "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
            ),
            "responseSigned": settings.get("response_signed", True),
            "assertionSigned": settings.get("assertion_signed", True),
            "signatureAlgorithm": settings.get("signature_algorithm", "RSA_SHA256"),
            "digestAlgorithm": settings.get("digest_algorithm", "SHA256"),
            "authnContextClassRef": settings.get(
                "authn_context_class_ref",
                "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
            ),
        }
        return {
            "label": label,
            "signOnMode": "SAML_2_0",
            "visibility": {"autoSubmitToolbar": False},
            "settings": {"signOn": sign_on},
        }
    if template == "bookmark":
        if "url" not in settings:
            raise ValueError("Bookmark template requires settings['url'].")
        return {
            "name": "bookmark",
            "label": label,
            "signOnMode": "BOOKMARK",
            "settings": {
                "app": {
                    "url": settings["url"],
                    "requestIntegration": settings.get("request_integration", False),
                }
            },
        }
    raise ValueError(
        f"Unknown app template {template!r}; expected one of {APP_TEMPLATES}."
    )


class Api(ApiClientBase):
    """Applications domain methods."""

    def list_apps(
        self,
        q: str | None = None,
        filter_expr: str | None = None,
        limit: int = APPS_PAGE_LIMIT,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """List applications with optional ``q`` label match or SCIM ``filter``.

        GET /api/v1/apps
        """
        params = drop_none(
            {"q": q, "filter": filter_expr, "limit": min(limit, APPS_PAGE_LIMIT)}
        )
        return self.paginate("/api/v1/apps", params=params, max_items=max_items)

    def get_app(self, app_id: str) -> dict[str, Any]:
        """Get one application by id.

        GET /api/v1/apps/{appId}
        """
        return self.envelope(self.request("GET", f"/api/v1/apps/{app_id}"))

    def create_app(
        self,
        template: str,
        label: str,
        settings: dict[str, Any] | None = None,
        activate: bool = True,
    ) -> dict[str, Any]:
        """Create an app from a basic template (``oidc``/``saml``/``bookmark``).

        POST /api/v1/apps?activate= — body built by
        :func:`build_app_template`.
        """
        body = build_app_template(template, label, settings)
        return self.envelope(
            self.request(
                "POST",
                "/api/v1/apps",
                params={"activate": "true" if activate else "false"},
                json_body=body,
            )
        )

    def update_app(self, app_id: str, app: dict[str, Any]) -> dict[str, Any]:
        """Replace an application (PUT semantics — pass the full app object).

        PUT /api/v1/apps/{appId} — Okta replaces the whole representation, so
        read with ``get`` first and send the modified object back.
        """
        return self.envelope(
            self.request("PUT", f"/api/v1/apps/{app_id}", json_body=app)
        )

    def activate_app(self, app_id: str) -> dict[str, Any]:
        """Activate an application.

        POST /api/v1/apps/{appId}/lifecycle/activate
        """
        return self.envelope(
            self.request("POST", f"/api/v1/apps/{app_id}/lifecycle/activate")
        )

    def deactivate_app(self, app_id: str) -> dict[str, Any]:
        """Deactivate an application — destructive.

        POST /api/v1/apps/{appId}/lifecycle/deactivate
        """
        return self.envelope(
            self.request("POST", f"/api/v1/apps/{app_id}/lifecycle/deactivate")
        )

    # ------------------------------------------------------------------ #
    # User assignments
    # ------------------------------------------------------------------ #

    def list_app_users(self, app_id: str, max_items: int = 1000) -> dict[str, Any]:
        """List the users assigned to an app.

        GET /api/v1/apps/{appId}/users
        """
        return self.paginate(f"/api/v1/apps/{app_id}/users", max_items=max_items)

    def assign_user_to_app(
        self, app_id: str, user_id: str, profile: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Assign a user to an app with an optional app-specific profile.

        POST /api/v1/apps/{appId}/users
        """
        body: dict[str, Any] = {"id": user_id, "scope": "USER"}
        if profile:
            body["profile"] = profile
        return self.envelope(
            self.request("POST", f"/api/v1/apps/{app_id}/users", json_body=body)
        )

    def unassign_user_from_app(self, app_id: str, user_id: str) -> dict[str, Any]:
        """Remove a user's app assignment — destructive.

        DELETE /api/v1/apps/{appId}/users/{userId}
        """
        return self.envelope(
            self.request("DELETE", f"/api/v1/apps/{app_id}/users/{user_id}")
        )

    # ------------------------------------------------------------------ #
    # Group assignments
    # ------------------------------------------------------------------ #

    def list_app_groups(self, app_id: str, max_items: int = 1000) -> dict[str, Any]:
        """List the groups assigned to an app.

        GET /api/v1/apps/{appId}/groups
        """
        return self.paginate(f"/api/v1/apps/{app_id}/groups", max_items=max_items)

    def assign_group_to_app(
        self, app_id: str, group_id: str, priority: int | None = None
    ) -> dict[str, Any]:
        """Assign a group to an app.

        PUT /api/v1/apps/{appId}/groups/{groupId}
        """
        body = {"priority": priority} if priority is not None else {}
        return self.envelope(
            self.request(
                "PUT", f"/api/v1/apps/{app_id}/groups/{group_id}", json_body=body
            )
        )

    def unassign_group_from_app(self, app_id: str, group_id: str) -> dict[str, Any]:
        """Remove a group's app assignment — destructive.

        DELETE /api/v1/apps/{appId}/groups/{groupId}
        """
        return self.envelope(
            self.request("DELETE", f"/api/v1/apps/{app_id}/groups/{group_id}")
        )
