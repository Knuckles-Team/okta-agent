"""CONCEPT:OK-OS.governance.okta Okta Users API client (lifecycle, credentials, related resources).

Mirrors the keycloak-agent users verb taxonomy (list/get/create/update,
reset_password, group membership) so agents can switch IdPs with familiar
verbs, plus Okta-specific lifecycle states (suspend/unlock/etc.).

API reference:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/User/
Lifecycle reference:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/UserLifecycle/
"""

from typing import Any

from okta_agent.api.api_client_base import ApiClientBase, drop_none
from okta_agent.api.filters import build_filter

#: Okta caps the users page size at 200.
USERS_PAGE_LIMIT = 200


class Api(ApiClientBase):
    """Users domain methods."""

    def list_users(
        self,
        q: str | None = None,
        filter_expr: str | None = None,
        search: str | None = None,
        limit: int = USERS_PAGE_LIMIT,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """List users with optional ``q`` prefix match, SCIM ``filter`` or ``search``.

        GET /api/v1/users — ``q`` matches firstName/lastName/email prefixes;
        ``filter`` supports a SCIM subset; ``search`` supports the richer
        search syntax (arbitrary profile attributes).
        """
        params = drop_none(
            {
                "q": q,
                "filter": filter_expr,
                "search": search,
                "limit": min(limit, USERS_PAGE_LIMIT),
            }
        )
        return self.paginate("/api/v1/users", params=params, max_items=max_items)

    def search_users(
        self,
        conditions: list[dict[str, Any]] | None = None,
        joiner: str = "and",
        q: str | None = None,
        limit: int = USERS_PAGE_LIMIT,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """Search users from structured SCIM conditions (built safely).

        Builds ``filter`` from ``conditions`` via
        :func:`okta_agent.api.filters.build_filter`; ``q`` may be combined.
        """
        filter_expr = build_filter(conditions, joiner) if conditions else None
        return self.list_users(
            q=q, filter_expr=filter_expr, limit=limit, max_items=max_items
        )

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Get one user by id, login, or login shortname.

        GET /api/v1/users/{userId}
        """
        return self.envelope(self.request("GET", f"/api/v1/users/{user_id}"))

    def create_user(
        self,
        profile: dict[str, Any],
        credentials: dict[str, Any] | None = None,
        group_ids: list[str] | None = None,
        activate: bool = True,
    ) -> dict[str, Any]:
        """Create a user, optionally activated immediately.

        POST /api/v1/users?activate={true|false} — ``profile`` must include
        at least ``firstName``, ``lastName``, ``email`` and ``login``.
        """
        body: dict[str, Any] = {"profile": profile}
        if credentials:
            body["credentials"] = credentials
        if group_ids:
            body["groupIds"] = group_ids
        return self.envelope(
            self.request(
                "POST",
                "/api/v1/users",
                params={"activate": _flag(activate)},
                json_body=body,
            )
        )

    def update_user(
        self,
        user_id: str,
        profile: dict[str, Any] | None = None,
        credentials: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Partially update a user's profile and/or credentials.

        POST /api/v1/users/{userId} (POST = partial update; PUT would replace
        the whole profile).
        """
        body = drop_none({"profile": profile, "credentials": credentials})
        return self.envelope(
            self.request("POST", f"/api/v1/users/{user_id}", json_body=body)
        )

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def activate_user(self, user_id: str, send_email: bool = False) -> dict[str, Any]:
        """Activate a STAGED/DEPROVISIONED user.

        POST /api/v1/users/{userId}/lifecycle/activate?sendEmail=
        """
        return self.envelope(
            self.request(
                "POST",
                f"/api/v1/users/{user_id}/lifecycle/activate",
                params={"sendEmail": _flag(send_email)},
            )
        )

    def deactivate_user(self, user_id: str, send_email: bool = False) -> dict[str, Any]:
        """Deactivate (deprovision) a user — destructive.

        POST /api/v1/users/{userId}/lifecycle/deactivate?sendEmail=
        """
        return self.envelope(
            self.request(
                "POST",
                f"/api/v1/users/{user_id}/lifecycle/deactivate",
                params={"sendEmail": _flag(send_email)},
            )
        )

    def suspend_user(self, user_id: str) -> dict[str, Any]:
        """Suspend an ACTIVE user — destructive.

        POST /api/v1/users/{userId}/lifecycle/suspend
        """
        return self.envelope(
            self.request("POST", f"/api/v1/users/{user_id}/lifecycle/suspend")
        )

    def unsuspend_user(self, user_id: str) -> dict[str, Any]:
        """Return a SUSPENDED user to ACTIVE.

        POST /api/v1/users/{userId}/lifecycle/unsuspend
        """
        return self.envelope(
            self.request("POST", f"/api/v1/users/{user_id}/lifecycle/unsuspend")
        )

    def unlock_user(self, user_id: str) -> dict[str, Any]:
        """Unlock a LOCKED_OUT user.

        POST /api/v1/users/{userId}/lifecycle/unlock
        """
        return self.envelope(
            self.request("POST", f"/api/v1/users/{user_id}/lifecycle/unlock")
        )

    # ------------------------------------------------------------------ #
    # Credentials
    # ------------------------------------------------------------------ #

    def expire_password(
        self, user_id: str, temp_password: bool = False
    ) -> dict[str, Any]:
        """Expire a user's password — destructive.

        POST /api/v1/users/{userId}/lifecycle/expire_password
        (or ``expire_password_with_temp_password`` when ``temp_password``).
        """
        suffix = (
            "expire_password_with_temp_password" if temp_password else "expire_password"
        )
        return self.envelope(
            self.request("POST", f"/api/v1/users/{user_id}/lifecycle/{suffix}")
        )

    def reset_password(self, user_id: str, send_email: bool = True) -> dict[str, Any]:
        """Start the password-reset flow — destructive.

        POST /api/v1/users/{userId}/lifecycle/reset_password?sendEmail= —
        with ``sendEmail=false`` Okta returns a one-time reset URL instead.
        """
        return self.envelope(
            self.request(
                "POST",
                f"/api/v1/users/{user_id}/lifecycle/reset_password",
                params={"sendEmail": _flag(send_email)},
            )
        )

    # ------------------------------------------------------------------ #
    # Related resources
    # ------------------------------------------------------------------ #

    def list_user_groups(self, user_id: str, max_items: int = 1000) -> dict[str, Any]:
        """List the groups a user belongs to.

        GET /api/v1/users/{userId}/groups
        """
        return self.paginate(f"/api/v1/users/{user_id}/groups", max_items=max_items)

    def list_user_apps(self, user_id: str) -> dict[str, Any]:
        """List the app links assigned to a user.

        GET /api/v1/users/{userId}/appLinks
        """
        return self.envelope(self.request("GET", f"/api/v1/users/{user_id}/appLinks"))

    def list_user_factors(self, user_id: str) -> dict[str, Any]:
        """List the enrolled MFA factors for a user.

        GET /api/v1/users/{userId}/factors
        """
        return self.envelope(self.request("GET", f"/api/v1/users/{user_id}/factors"))

    def clear_user_sessions(
        self, user_id: str, oauth_tokens: bool = False
    ) -> dict[str, Any]:
        """Revoke all of a user's sessions — destructive.

        DELETE /api/v1/users/{userId}/sessions?oauthTokens= — when
        ``oauth_tokens`` is true, also revokes OIDC/OAuth tokens.
        """
        return self.envelope(
            self.request(
                "DELETE",
                f"/api/v1/users/{user_id}/sessions",
                params={"oauthTokens": _flag(oauth_tokens)},
            )
        )


def _flag(value: bool) -> str:
    """Render a boolean as Okta's lowercase query-param literal."""
    return "true" if value else "false"
