"""Surface contracts: tool use, links, data locations and business roles."""

from scion_sdk.surface_contracts import (
    BusinessRole,
    DataLocation,
    Refusal,
    SurfaceLink,
    ToolStep,
    ToolUseContract,
)

_ACCESS_DENIED = Refusal(
    "ACCESS_DENIED", "the token or OAuth scope lacks permission for the operation"
)
_NOT_FOUND = Refusal(
    "NOT_FOUND", "the user, group, application or policy does not exist"
)
_INVALID_ARGUMENT = Refusal(
    "INVALID_ARGUMENT", "Okta rejects the profile, expression or filter"
)
_INVALID_STATE = Refusal(
    "INVALID_STATE", "the object is not in a lifecycle state that allows the transition"
)
_DESTRUCTIVE_BLOCKED = Refusal(
    "DESTRUCTIVE_BLOCKED",
    "the caller did not confirm the destructive operation",
)
_RATE_LIMITED = Refusal(
    "RATE_LIMITED", "the org rate limit is exhausted after the capped backoff"
)
_NO_ENGINE = Refusal(
    "NO_ENGINE", "no knowledge-graph engine is reachable, so ingested is null"
)

CONTRACTS = (
    ToolUseContract(
        "find-users",
        (
            ToolStep(
                "okta_list_users",
                params=("q", "filter_expr", "search", "limit", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _RATE_LIMITED),
            ),
            ToolStep(
                "okta_search_users",
                params=("conditions", "joiner", "q", "limit", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _RATE_LIMITED),
            ),
            ToolStep(
                "okta_get_user",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
        ),
        "Find users by prefix or structured conditions and read one in full.",
    ),
    ToolUseContract(
        "onboard-user",
        (
            ToolStep(
                "okta_search_users",
                params=("conditions", "joiner"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_create_user",
                params=("profile", "credentials", "group_ids", "activate"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_add_group_member",
                params=("group_id", "user_id"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_assign_user_to_app",
                params=("app_id", "user_id", "profile"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _NOT_FOUND),
            ),
            ToolStep(
                "okta_activate_user",
                params=("user_id", "send_email"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_list_user_groups",
                params=("user_id", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
        ),
        "Create a user, place them in groups and apps, and activate them.",
    ),
    ToolUseContract(
        "update-user-profile",
        (
            ToolStep(
                "okta_get_user",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_update_user",
                params=("user_id", "profile", "credentials"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _NOT_FOUND),
            ),
        ),
        "Read a user and apply a partial profile update.",
    ),
    ToolUseContract(
        "recover-user-access",
        (
            ToolStep(
                "okta_get_user",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_list_user_factors",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_unlock_user",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_unsuspend_user",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_expire_password",
                params=("user_id", "temp_password", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_reset_password",
                params=("user_id", "send_email", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
        ),
        "Unlock, unsuspend or reset the credentials of a user who cannot sign in.",
    ),
    ToolUseContract(
        "offboard-user",
        (
            ToolStep(
                "okta_get_user",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_list_user_groups",
                params=("user_id", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_list_user_apps",
                params=("user_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_clear_user_sessions",
                params=("user_id", "oauth_tokens", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_remove_group_member",
                params=("group_id", "user_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_unassign_user_from_app",
                params=("app_id", "user_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_suspend_user",
                params=("user_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(
                    _ACCESS_DENIED,
                    _NOT_FOUND,
                    _DESTRUCTIVE_BLOCKED,
                    _INVALID_STATE,
                ),
            ),
            ToolStep(
                "okta_deactivate_user",
                params=("user_id", "send_email", "confirm"),
                result=("data", "rate_limit"),
                refusals=(
                    _ACCESS_DENIED,
                    _NOT_FOUND,
                    _DESTRUCTIVE_BLOCKED,
                    _INVALID_STATE,
                ),
            ),
        ),
        "Revoke a leaver's sessions and access, then deactivate the account.",
    ),
    ToolUseContract(
        "manage-group-membership",
        (
            ToolStep(
                "okta_list_groups",
                params=("q", "filter_expr", "search", "limit", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_search_groups",
                params=("conditions", "joiner", "q", "limit", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_get_group",
                params=("group_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_create_group",
                params=("name", "description"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_update_group",
                params=("group_id", "name", "description"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _NOT_FOUND),
            ),
            ToolStep(
                "okta_list_group_members",
                params=("group_id", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_add_group_member",
                params=("group_id", "user_id"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_remove_group_member",
                params=("group_id", "user_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_delete_group",
                params=("group_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
        ),
        "Find or create a group and change who belongs to it.",
    ),
    ToolUseContract(
        "automate-group-rules",
        (
            ToolStep(
                "okta_list_group_rules",
                params=("search", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_create_group_rule",
                params=("name", "expression", "assign_group_ids"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_activate_group_rule",
                params=("rule_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_deactivate_group_rule",
                params=("rule_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
        ),
        "Author dynamic membership rules and switch them on or off.",
    ),
    ToolUseContract(
        "manage-application-access",
        (
            ToolStep(
                "okta_list_apps",
                params=("q", "filter_expr", "limit", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_get_app",
                params=("app_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_create_app",
                params=("template", "label", "settings", "activate"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_update_app",
                params=("app_id", "app"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _NOT_FOUND),
            ),
            ToolStep(
                "okta_activate_app",
                params=("app_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_deactivate_app",
                params=("app_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_list_app_users",
                params=("app_id", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_assign_user_to_app",
                params=("app_id", "user_id", "profile"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _NOT_FOUND),
            ),
            ToolStep(
                "okta_unassign_user_from_app",
                params=("app_id", "user_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_list_app_groups",
                params=("app_id", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_assign_group_to_app",
                params=("app_id", "group_id", "priority"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _NOT_FOUND),
            ),
            ToolStep(
                "okta_unassign_group_from_app",
                params=("app_id", "group_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
        ),
        "Create and maintain application integrations and who is assigned to them.",
    ),
    ToolUseContract(
        "review-policies",
        (
            ToolStep(
                "okta_list_policies",
                params=("policy_type", "status", "max_items"),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT),
            ),
            ToolStep(
                "okta_get_policy",
                params=("policy_id", "with_rules"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_list_policy_rules",
                params=("policy_id",),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND),
            ),
            ToolStep(
                "okta_activate_policy",
                params=("policy_id",),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_deactivate_policy",
                params=("policy_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
            ToolStep(
                "okta_activate_policy_rule",
                params=("policy_id", "rule_id"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _INVALID_STATE),
            ),
            ToolStep(
                "okta_deactivate_policy_rule",
                params=("policy_id", "rule_id", "confirm"),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED, _NOT_FOUND, _DESTRUCTIVE_BLOCKED),
            ),
        ),
        "Read access policies and their rules, and switch a policy or rule on or off.",
    ),
    ToolUseContract(
        "investigate-activity",
        (
            ToolStep(
                "okta_get_org",
                params=(),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED,),
            ),
            ToolStep(
                "okta_get_system_log",
                params=(
                    "since",
                    "until",
                    "filter_expr",
                    "q",
                    "limit",
                    "max_items",
                    "sort_order",
                ),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED, _INVALID_ARGUMENT, _RATE_LIMITED),
            ),
            ToolStep(
                "okta_list_authenticators",
                params=(),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED,),
            ),
            ToolStep(
                "okta_list_org_factors",
                params=(),
                result=("data", "rate_limit"),
                refusals=(_ACCESS_DENIED,),
            ),
            ToolStep(
                "okta_list_network_zones",
                params=("max_items",),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED,),
            ),
            ToolStep(
                "okta_list_authorization_servers",
                params=("max_items",),
                result=("data", "count", "truncated", "next_cursor"),
                refusals=(_ACCESS_DENIED,),
            ),
        ),
        "Read the audit trail and the org's authentication posture.",
    ),
    ToolUseContract(
        "capture-directory-to-graph",
        (
            ToolStep(
                "okta_ingest_users",
                params=("limit", "max_items"),
                result=("listed", "ingested"),
                refusals=(_ACCESS_DENIED, _NO_ENGINE),
            ),
            ToolStep(
                "okta_ingest_groups",
                params=("limit", "max_items"),
                result=("listed", "ingested"),
                refusals=(_ACCESS_DENIED, _NO_ENGINE),
            ),
            ToolStep(
                "okta_ingest_apps",
                params=("limit", "max_items"),
                result=("listed", "ingested"),
                refusals=(_ACCESS_DENIED, _NO_ENGINE),
            ),
            ToolStep(
                "okta_ingest_all",
                params=("limit", "max_items"),
                result=("users", "groups", "apps"),
                refusals=(_ACCESS_DENIED, _NO_ENGINE),
            ),
        ),
        "Mirror users, groups and applications into the knowledge graph.",
    ),
)

LINKS = (
    SurfaceLink(
        "find-users",
        tools=("okta_list_users", "okta_search_users", "okta_get_user"),
        prompts=(
            "okta-operator",
            "okta-identity-administrator",
            "okta-security-auditor",
        ),
        skills=("okta-user-lifecycle",),
    ),
    SurfaceLink(
        "onboard-user",
        tools=(
            "okta_search_users",
            "okta_create_user",
            "okta_add_group_member",
            "okta_assign_user_to_app",
            "okta_activate_user",
            "okta_list_user_groups",
        ),
        prompts=("okta-operator", "okta-identity-administrator"),
        skills=("okta-user-lifecycle", "okta-access-management"),
    ),
    SurfaceLink(
        "update-user-profile",
        tools=("okta_get_user", "okta_update_user"),
        prompts=("okta-operator", "okta-identity-administrator"),
        skills=("okta-user-lifecycle",),
    ),
    SurfaceLink(
        "recover-user-access",
        tools=(
            "okta_get_user",
            "okta_list_user_factors",
            "okta_unlock_user",
            "okta_unsuspend_user",
            "okta_expire_password",
            "okta_reset_password",
        ),
        prompts=("okta-operator", "okta-identity-administrator"),
        skills=("okta-user-lifecycle",),
    ),
    SurfaceLink(
        "offboard-user",
        tools=(
            "okta_get_user",
            "okta_list_user_groups",
            "okta_list_user_apps",
            "okta_clear_user_sessions",
            "okta_remove_group_member",
            "okta_unassign_user_from_app",
            "okta_suspend_user",
            "okta_deactivate_user",
        ),
        prompts=("okta-operator", "okta-identity-administrator"),
        skills=("okta-user-lifecycle", "okta-access-management"),
    ),
    SurfaceLink(
        "manage-group-membership",
        tools=(
            "okta_list_groups",
            "okta_search_groups",
            "okta_get_group",
            "okta_create_group",
            "okta_update_group",
            "okta_list_group_members",
            "okta_add_group_member",
            "okta_remove_group_member",
            "okta_delete_group",
        ),
        prompts=("okta-operator", "okta-access-manager"),
        skills=("okta-access-management",),
    ),
    SurfaceLink(
        "automate-group-rules",
        tools=(
            "okta_list_group_rules",
            "okta_create_group_rule",
            "okta_activate_group_rule",
            "okta_deactivate_group_rule",
        ),
        prompts=("okta-operator", "okta-access-manager"),
        skills=("okta-access-management",),
    ),
    SurfaceLink(
        "manage-application-access",
        tools=(
            "okta_list_apps",
            "okta_get_app",
            "okta_create_app",
            "okta_update_app",
            "okta_activate_app",
            "okta_deactivate_app",
            "okta_list_app_users",
            "okta_assign_user_to_app",
            "okta_unassign_user_from_app",
            "okta_list_app_groups",
            "okta_assign_group_to_app",
            "okta_unassign_group_from_app",
        ),
        prompts=("okta-operator", "okta-access-manager"),
        skills=("okta-access-management",),
    ),
    SurfaceLink(
        "review-policies",
        tools=(
            "okta_list_policies",
            "okta_get_policy",
            "okta_list_policy_rules",
            "okta_activate_policy",
            "okta_deactivate_policy",
            "okta_activate_policy_rule",
            "okta_deactivate_policy_rule",
        ),
        prompts=("okta-operator", "okta-access-manager", "okta-security-auditor"),
        skills=("okta-agent-operations",),
    ),
    SurfaceLink(
        "investigate-activity",
        tools=(
            "okta_get_org",
            "okta_get_system_log",
            "okta_list_authenticators",
            "okta_list_org_factors",
            "okta_list_network_zones",
            "okta_list_authorization_servers",
        ),
        prompts=("okta-operator", "okta-security-auditor"),
        skills=("okta-agent-operations",),
    ),
    SurfaceLink(
        "capture-directory-to-graph",
        tools=(
            "okta_ingest_users",
            "okta_ingest_groups",
            "okta_ingest_apps",
            "okta_ingest_all",
        ),
        prompts=("okta-operator", "okta-security-auditor"),
        skills=("okta-directory-ingestion",),
    ),
    SurfaceLink(
        "okta-agent-operations",
        tools=(
            "okta_list_users",
            "okta_search_users",
            "okta_get_user",
            "okta_create_user",
            "okta_add_group_member",
            "okta_assign_user_to_app",
            "okta_activate_user",
            "okta_list_user_groups",
            "okta_update_user",
            "okta_list_user_factors",
            "okta_unlock_user",
            "okta_unsuspend_user",
            "okta_expire_password",
            "okta_reset_password",
            "okta_list_user_apps",
            "okta_clear_user_sessions",
            "okta_remove_group_member",
            "okta_unassign_user_from_app",
            "okta_suspend_user",
            "okta_deactivate_user",
            "okta_list_groups",
            "okta_search_groups",
            "okta_get_group",
            "okta_create_group",
            "okta_update_group",
            "okta_list_group_members",
            "okta_delete_group",
            "okta_list_group_rules",
            "okta_create_group_rule",
            "okta_activate_group_rule",
            "okta_deactivate_group_rule",
            "okta_list_apps",
            "okta_get_app",
            "okta_create_app",
            "okta_update_app",
            "okta_activate_app",
            "okta_deactivate_app",
            "okta_list_app_users",
            "okta_list_app_groups",
            "okta_assign_group_to_app",
            "okta_unassign_group_from_app",
            "okta_list_policies",
            "okta_get_policy",
            "okta_list_policy_rules",
            "okta_activate_policy",
            "okta_deactivate_policy",
            "okta_activate_policy_rule",
            "okta_deactivate_policy_rule",
            "okta_get_org",
            "okta_get_system_log",
            "okta_list_authenticators",
            "okta_list_org_factors",
            "okta_list_network_zones",
            "okta_list_authorization_servers",
            "okta_ingest_users",
            "okta_ingest_groups",
            "okta_ingest_apps",
            "okta_ingest_all",
        ),
        skills=("okta-agent-operations",),
    ),
)

LOCATIONS = (
    DataLocation(
        "okta-users",
        ("User", "Factor"),
        "OKTA_ORG_URL",
        "okta_list_users",
        federation_key="id",
    ),
    DataLocation(
        "okta-groups",
        ("Group", "GroupRule"),
        "OKTA_ORG_URL",
        "okta_list_groups",
        federation_key="id",
    ),
    DataLocation(
        "okta-applications",
        ("Application",),
        "OKTA_ORG_URL",
        "okta_list_apps",
        federation_key="id",
    ),
    DataLocation(
        "okta-policies",
        ("Policy",),
        "OKTA_ORG_URL",
        "okta_list_policies",
        federation_key="id",
    ),
    DataLocation(
        "okta-system-log",
        ("LogEvent",),
        "OKTA_ORG_URL",
        "okta_get_system_log",
        federation_key="uuid",
    ),
)

ROLES = (
    BusinessRole(
        "identity-administrator",
        tasks=(
            "find-users",
            "onboard-user",
            "update-user-profile",
            "recover-user-access",
            "offboard-user",
        ),
    ),
    BusinessRole(
        "access-manager",
        tasks=(
            "manage-group-membership",
            "automate-group-rules",
            "manage-application-access",
            "review-policies",
        ),
    ),
    BusinessRole(
        "security-auditor",
        tasks=(
            "find-users",
            "review-policies",
            "investigate-activity",
            "capture-directory-to-graph",
        ),
    ),
)
