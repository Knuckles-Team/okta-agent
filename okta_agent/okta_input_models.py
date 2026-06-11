"""CONCEPT:OKTA-1.3 Typed input models for the Okta tool surface.

Pydantic models mirroring the ``params_json`` contracts of the action-routed
MCP tools in :mod:`okta_agent.mcp`. Programmatic callers can build and
validate tool parameters with these models, then pass
``model.model_dump_json(exclude_none=True)`` as ``params_json``.
"""

from typing import Any

from pydantic import BaseModel, Field


class FilterCondition(BaseModel):
    """One SCIM filter clause for ``search`` actions (CONCEPT:OKTA-1.5)."""

    field: str = Field(description='Attribute path, e.g. "profile.department".')
    op: str = Field(description="SCIM operator: eq, sw, gt, ge, lt, le, pr.")
    value: Any = Field(default=None, description="Comparison value (omit for pr).")


class SearchInput(BaseModel):
    """``search`` parameters for the users/groups tools."""

    conditions: list[FilterCondition] = Field(
        description="Filter clauses, joined with the joiner."
    )
    joiner: str = Field(default="and", description='Clause joiner: "and" or "or".')
    limit: int | None = Field(default=None, description="Page size.")
    max_items: int | None = Field(default=None, description="Hard item cap.")


class ListInput(BaseModel):
    """Generic ``list`` parameters (cursor pagination)."""

    q: str | None = Field(default=None, description="Simple name/keyword query.")
    limit: int | None = Field(default=None, description="Page size.")
    after: str | None = Field(default=None, description="Resume cursor.")
    max_items: int | None = Field(default=None, description="Hard item cap.")


class UserRefInput(BaseModel):
    """Single-user actions: get/activate/deactivate/suspend/unlock/etc."""

    user_id: str = Field(description="Okta user id (or login for get).")


class UserCreateInput(BaseModel):
    """``okta_users`` create parameters."""

    profile: dict[str, Any] = Field(
        description="Okta user profile (firstName, lastName, email, login, ...)."
    )
    credentials: dict[str, Any] | None = Field(
        default=None, description="Optional credentials object."
    )
    activate: bool = Field(default=True, description="Activate on creation.")


class UserUpdateInput(BaseModel):
    """``okta_users`` update parameters (partial profile update)."""

    user_id: str = Field(description="Okta user id.")
    profile: dict[str, Any] = Field(description="Profile attributes to update.")


class GroupRefInput(BaseModel):
    """Single-group actions: get/delete/list_members/list_rules."""

    group_id: str = Field(description="Okta group id.")


class GroupCreateInput(BaseModel):
    """``okta_groups`` create/update parameters."""

    name: str = Field(description="Group name.")
    description: str | None = Field(default=None, description="Group description.")


class GroupMemberInput(BaseModel):
    """``okta_groups`` add_member/remove_member parameters."""

    group_id: str = Field(description="Okta group id.")
    user_id: str = Field(description="Okta user id.")


class AppRefInput(BaseModel):
    """Single-app actions: get/activate/deactivate/list_users/list_groups."""

    app_id: str = Field(description="Okta application id.")


class AppCreateInput(BaseModel):
    """``okta_apps`` create parameters (oidc/saml/bookmark templates)."""

    template: str = Field(description='App template: "oidc", "saml" or "bookmark".')
    label: str = Field(description="Display label for the application.")
    settings: dict[str, Any] = Field(
        default_factory=dict, description="Template-specific settings."
    )


class AppAssignmentInput(BaseModel):
    """``okta_apps`` assign/unassign user or group parameters."""

    app_id: str = Field(description="Okta application id.")
    user_id: str | None = Field(default=None, description="User to (un)assign.")
    group_id: str | None = Field(default=None, description="Group to (un)assign.")


class PolicyListInput(BaseModel):
    """``okta_policies`` list parameters."""

    policy_type: str = Field(
        description=(
            "Policy type: okta_sign_on, password, mfa_enroll or access_policy."
        )
    )


class PolicyRefInput(BaseModel):
    """Single-policy actions: get/list_rules/activate/deactivate."""

    policy_id: str = Field(description="Okta policy id.")


class PolicyRuleRefInput(BaseModel):
    """``okta_policies`` activate_rule/deactivate_rule parameters."""

    policy_id: str = Field(description="Okta policy id.")
    rule_id: str = Field(description="Okta policy rule id.")


class SystemLogInput(BaseModel):
    """``okta_system`` logs parameters."""

    since: str | None = Field(default=None, description="ISO-8601 lower bound.")
    until: str | None = Field(default=None, description="ISO-8601 upper bound.")
    filter: str | None = Field(default=None, description="SCIM filter expression.")
    q: str | None = Field(default=None, description="Keyword query.")
    limit: int | None = Field(default=None, description="Page size.")
    after: str | None = Field(default=None, description="Resume cursor.")
    max_items: int | None = Field(
        default=None, description="Hard event cap (tool caps at 1000)."
    )
