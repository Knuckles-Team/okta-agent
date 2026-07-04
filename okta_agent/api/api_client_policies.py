"""CONCEPT:OK-OS.governance.okta Okta Policies API client (read + lifecycle only).

Scope note: policy/rule **create and update are intentionally out of scope in
this connector's first release** — Okta policy documents are deeply nested and
type-specific, and a malformed write can lock an org out. This module reads
policies/rules and toggles their lifecycle (activate/deactivate) only.

API reference:
https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Policy/
"""

from typing import Any

from okta_agent.api.api_client_base import ApiClientBase, drop_none

#: Friendly aliases → Okta policy type identifiers.
POLICY_TYPES = {
    "okta_sign_on": "OKTA_SIGN_ON",
    "password": "PASSWORD",  # nosec B105 - policy type id, not a credential
    "mfa_enroll": "MFA_ENROLL",
    "access_policy": "ACCESS_POLICY",
}


def resolve_policy_type(policy_type: str) -> str:
    """Map a friendly alias (or exact identifier) to an Okta policy type."""
    key = policy_type.strip().lower()
    if key in POLICY_TYPES:
        return POLICY_TYPES[key]
    upper = policy_type.strip().upper()
    if upper in POLICY_TYPES.values():
        return upper
    raise ValueError(
        f"Unknown policy type {policy_type!r}; expected one of "
        f"{sorted(POLICY_TYPES)} (or the uppercase Okta identifiers)."
    )


class Api(ApiClientBase):
    """Policies domain methods."""

    def list_policies(
        self,
        policy_type: str,
        status: str | None = None,
        max_items: int = 1000,
    ) -> dict[str, Any]:
        """List policies of one type (``okta_sign_on``/``password``/``mfa_enroll``/``access_policy``).

        GET /api/v1/policies?type={type}&status=
        """
        params = drop_none({"type": resolve_policy_type(policy_type), "status": status})
        return self.paginate("/api/v1/policies", params=params, max_items=max_items)

    def get_policy(self, policy_id: str, with_rules: bool = False) -> dict[str, Any]:
        """Get one policy, optionally expanded with its rules.

        GET /api/v1/policies/{policyId}?expand=rules
        """
        params = {"expand": "rules"} if with_rules else None
        return self.envelope(
            self.request("GET", f"/api/v1/policies/{policy_id}", params=params)
        )

    def list_policy_rules(self, policy_id: str) -> dict[str, Any]:
        """List the rules of a policy.

        GET /api/v1/policies/{policyId}/rules
        """
        return self.envelope(self.request("GET", f"/api/v1/policies/{policy_id}/rules"))

    def activate_policy(self, policy_id: str) -> dict[str, Any]:
        """Activate a policy.

        POST /api/v1/policies/{policyId}/lifecycle/activate
        """
        return self.envelope(
            self.request("POST", f"/api/v1/policies/{policy_id}/lifecycle/activate")
        )

    def deactivate_policy(self, policy_id: str) -> dict[str, Any]:
        """Deactivate a policy — destructive.

        POST /api/v1/policies/{policyId}/lifecycle/deactivate
        """
        return self.envelope(
            self.request("POST", f"/api/v1/policies/{policy_id}/lifecycle/deactivate")
        )

    def activate_policy_rule(self, policy_id: str, rule_id: str) -> dict[str, Any]:
        """Activate a policy rule.

        POST /api/v1/policies/{policyId}/rules/{ruleId}/lifecycle/activate
        """
        return self.envelope(
            self.request(
                "POST",
                f"/api/v1/policies/{policy_id}/rules/{rule_id}/lifecycle/activate",
            )
        )

    def deactivate_policy_rule(self, policy_id: str, rule_id: str) -> dict[str, Any]:
        """Deactivate a policy rule — destructive.

        POST /api/v1/policies/{policyId}/rules/{ruleId}/lifecycle/deactivate
        """
        return self.envelope(
            self.request(
                "POST",
                f"/api/v1/policies/{policy_id}/rules/{rule_id}/lifecycle/deactivate",
            )
        )
