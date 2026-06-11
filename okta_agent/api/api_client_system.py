"""CONCEPT:OKTA-1.1 Okta org/system API client (org, auth servers, system log, zones).

The system log query is hard-capped (page ``limit`` <= 1000, overall items
<= ``SYSTEM_LOG_MAX_ITEMS``) so an agent can never stream an unbounded audit
trail into its context window.

API references:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/OrgSetting/
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/AuthorizationServer/
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/SystemLog/
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Authenticator/
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/NetworkZone/
"""

from typing import Any

from okta_agent.api.api_client_base import ApiClientBase, drop_none

#: Okta's per-page maximum for /api/v1/logs.
SYSTEM_LOG_PAGE_LIMIT = 1000
#: Default page size for system log queries.
SYSTEM_LOG_DEFAULT_LIMIT = 100
#: Hard overall cap on returned log events per call.
SYSTEM_LOG_MAX_ITEMS = 1000


class Api(ApiClientBase):
    """Org/system domain methods."""

    def get_org(self) -> dict[str, Any]:
        """Get the org settings (company info, subdomain, status).

        GET /api/v1/org
        """
        return self.envelope(self.request("GET", "/api/v1/org"))

    def list_authorization_servers(self, max_items: int = 1000) -> dict[str, Any]:
        """List custom authorization servers.

        GET /api/v1/authorizationServers
        """
        return self.paginate("/api/v1/authorizationServers", max_items=max_items)

    def get_system_log(
        self,
        since: str | None = None,
        until: str | None = None,
        filter_expr: str | None = None,
        q: str | None = None,
        limit: int = SYSTEM_LOG_DEFAULT_LIMIT,
        max_items: int = SYSTEM_LOG_MAX_ITEMS,
        sort_order: str | None = None,
    ) -> dict[str, Any]:
        """Query the system log (audit events), capped and cursor-paginated.

        GET /api/v1/logs — ``since``/``until`` are ISO-8601 timestamps,
        ``filter`` is a SCIM expression over event fields (e.g.
        ``eventType eq "user.session.start"``), ``q`` is keyword search.
        ``limit`` is clamped to 1000 per page and total results are capped at
        ``max_items`` (never above ``SYSTEM_LOG_MAX_ITEMS``); the envelope's
        ``next_cursor`` resumes a truncated query.
        """
        params = drop_none(
            {
                "since": since,
                "until": until,
                "filter": filter_expr,
                "q": q,
                "limit": max(1, min(limit, SYSTEM_LOG_PAGE_LIMIT)),
                "sortOrder": sort_order,
            }
        )
        capped_max = max(1, min(max_items, SYSTEM_LOG_MAX_ITEMS))
        return self.paginate("/api/v1/logs", params=params, max_items=capped_max)

    def list_authenticators(self) -> dict[str, Any]:
        """List the org's authenticators (Okta Verify, WebAuthn, password, ...).

        GET /api/v1/authenticators
        """
        return self.envelope(self.request("GET", "/api/v1/authenticators"))

    def list_org_factors(self) -> dict[str, Any]:
        """List org-level MFA factor enablement (legacy Factors API view).

        GET /api/v1/org/factors
        """
        return self.envelope(self.request("GET", "/api/v1/org/factors"))

    def list_network_zones(self, max_items: int = 1000) -> dict[str, Any]:
        """List network zones.

        GET /api/v1/zones
        """
        return self.paginate("/api/v1/zones", max_items=max_items)
