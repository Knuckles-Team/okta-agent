"""CONCEPT:OK-OS.governance.okta Okta Groups API client (groups, membership, group rules).

Mirrors the keycloak-agent groups verb taxonomy (list/get/create/update/delete,
member add/remove) so agents can switch IdPs with familiar verbs; group rules
are the Okta-specific dynamic-membership feature.

API reference:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Group/
Group rules:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/GroupRule/
"""

from typing import Any

from okta_agent.api.api_client_base import ApiClientBase, drop_none
from okta_agent.api.filters import build_filter

#: Okta groups list page size cap (Okta allows up to 10000; 200 keeps pages light).
GROUPS_PAGE_LIMIT = 200


class Api(ApiClientBase):
    """Groups domain methods."""

    def list_groups(
        self,
        q: str | None = None,
        filter_expr: str | None = None,
        search: str | None = None,
        limit: int = GROUPS_PAGE_LIMIT,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """List groups with optional ``q`` name prefix, SCIM ``filter`` or ``search``.

        GET /api/v1/groups
        """
        params = drop_none(
            {
                "q": q,
                "filter": filter_expr,
                "search": search,
                "limit": min(limit, GROUPS_PAGE_LIMIT),
            }
        )
        return self.paginate("/api/v1/groups", params=params, max_items=max_items)

    def search_groups(
        self,
        conditions: list[dict[str, Any]] | None = None,
        joiner: str = "and",
        q: str | None = None,
        limit: int = GROUPS_PAGE_LIMIT,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """Search groups from structured SCIM conditions (built safely)."""
        filter_expr = build_filter(conditions, joiner) if conditions else None
        return self.list_groups(
            q=q, filter_expr=filter_expr, limit=limit, max_items=max_items
        )

    def get_group(self, group_id: str) -> dict[str, Any]:
        """Get one group by id.

        GET /api/v1/groups/{groupId}
        """
        return self.envelope(self.request("GET", f"/api/v1/groups/{group_id}"))

    def create_group(self, name: str, description: str | None = None) -> dict[str, Any]:
        """Create an OKTA_GROUP.

        POST /api/v1/groups
        """
        profile = drop_none({"name": name, "description": description})
        return self.envelope(
            self.request("POST", "/api/v1/groups", json_body={"profile": profile})
        )

    def update_group(
        self, group_id: str, name: str, description: str | None = None
    ) -> dict[str, Any]:
        """Replace a group's profile (PUT semantics — name is required).

        PUT /api/v1/groups/{groupId}
        """
        profile = drop_none({"name": name, "description": description})
        return self.envelope(
            self.request(
                "PUT", f"/api/v1/groups/{group_id}", json_body={"profile": profile}
            )
        )

    def delete_group(self, group_id: str) -> dict[str, Any]:
        """Delete a group — destructive.

        DELETE /api/v1/groups/{groupId}
        """
        return self.envelope(self.request("DELETE", f"/api/v1/groups/{group_id}"))

    # ------------------------------------------------------------------ #
    # Membership
    # ------------------------------------------------------------------ #

    def list_group_members(
        self, group_id: str, max_items: int = 1000
    ) -> dict[str, Any]:
        """List the users in a group.

        GET /api/v1/groups/{groupId}/users
        """
        return self.paginate(f"/api/v1/groups/{group_id}/users", max_items=max_items)

    def add_group_member(self, group_id: str, user_id: str) -> dict[str, Any]:
        """Add a user to a group.

        PUT /api/v1/groups/{groupId}/users/{userId}
        """
        return self.envelope(
            self.request("PUT", f"/api/v1/groups/{group_id}/users/{user_id}")
        )

    def remove_group_member(self, group_id: str, user_id: str) -> dict[str, Any]:
        """Remove a user from a group — destructive.

        DELETE /api/v1/groups/{groupId}/users/{userId}
        """
        return self.envelope(
            self.request("DELETE", f"/api/v1/groups/{group_id}/users/{user_id}")
        )

    # ------------------------------------------------------------------ #
    # Group rules (dynamic membership)
    # ------------------------------------------------------------------ #

    def list_group_rules(
        self, search: str | None = None, max_items: int = 1000
    ) -> dict[str, Any]:
        """List group rules.

        GET /api/v1/groups/rules
        """
        params = drop_none({"search": search})
        return self.paginate("/api/v1/groups/rules", params=params, max_items=max_items)

    def create_group_rule(
        self, name: str, expression: str, assign_group_ids: list[str]
    ) -> dict[str, Any]:
        """Create an INACTIVE group rule from an Okta Expression Language condition.

        POST /api/v1/groups/rules — ``expression`` uses Okta Expression
        Language (e.g. ``user.department=="Engineering"``); matching users are
        assigned to ``assign_group_ids``. Activate it separately.
        """
        body = {
            "type": "group_rule",
            "name": name,
            "conditions": {
                "expression": {
                    "type": "urn:okta:expression:1.0",
                    "value": expression,
                }
            },
            "actions": {"assignUserToGroups": {"groupIds": assign_group_ids}},
        }
        return self.envelope(
            self.request("POST", "/api/v1/groups/rules", json_body=body)
        )

    def activate_group_rule(self, rule_id: str) -> dict[str, Any]:
        """Activate a group rule.

        POST /api/v1/groups/rules/{ruleId}/lifecycle/activate
        """
        return self.envelope(
            self.request("POST", f"/api/v1/groups/rules/{rule_id}/lifecycle/activate")
        )

    def deactivate_group_rule(self, rule_id: str) -> dict[str, Any]:
        """Deactivate a group rule — destructive.

        POST /api/v1/groups/rules/{ruleId}/lifecycle/deactivate
        """
        return self.envelope(
            self.request("POST", f"/api/v1/groups/rules/{rule_id}/lifecycle/deactivate")
        )
