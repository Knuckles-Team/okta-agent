---
name: okta-access-management
skill_type: skill
description: >-
  Okta group and application access via the okta-agent MCP server: manage groups, membership, dynamic group rules and app assignments. Use to grant or revoke access. Do NOT use for user lifecycle or credentials (okta-user-lifecycle) or KG mirroring (okta-directory-ingestion).
license: MIT
tags: [okta, groups, applications, access, sso, rbac, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# Okta Access Management

Scope: Okta group and application access administration via the okta-agent MCP server — manage groups and their membership, dynamic group rules (Okta Expression Language), application integrations, and user/group-to-app assignments. Use when the agent must grant or revoke access by adding users to groups, wiring dynamic group rules, or assigning users/groups to SSO applications. Do NOT use for individual user lifecycle/credentials (okta-user-lifecycle) or KG mirroring (okta-directory-ingestion).

Domain-typed access to the Okta **Groups**, **Group Rules** and **Applications**
APIs for access administration — the join between identities and the resources
they can reach. Prefer the typed group and application tools.

## When to use
- Create/read/update/delete groups; list or change membership.
- Author dynamic **group rules** (Okta Expression Language) and activate/deactivate them.
- List/read/create/update application integrations and their lifecycle.
- Assign or unassign **users** and **groups** to/from applications.

## When NOT to use
- User profile CRUD, lifecycle, credentials, or MFA factors → `okta-user-lifecycle`.
- Sign-on / password / MFA-enroll **policies** → the `okta_list_policies` and `okta_get_policy` tools.
- Bulk mirroring of directory objects into the KG → `okta-directory-ingestion`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`okta-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `OKTA_ORG_URL` | ✅ | Org base URL, e.g. `https://acme.okta.com` |
| `OKTA_API_TOKEN` | ✅ | SSWS API token (or OAuth client creds) |

## Steps

1. Find the target group with `okta_search_groups` or `okta_list_groups`. Verify the returned `group_id` matches the intended group name.
2. Read current membership with `okta_list_group_members` (`group_id`). Verify whether the user is already a member.
3. Grant access with `okta_add_group_member` (`group_id`, `user_id`). Verify `okta_list_group_members` now includes the user.
4. For dynamic membership, call `okta_create_group_rule` (`name`, `expression`, `assign_group_ids`). Verify `okta_list_group_rules` shows the new rule as INACTIVE.
5. Turn the rule on with `okta_activate_group_rule` (`rule_id`). Verify `okta_list_group_rules` shows it ACTIVE.
6. Assign the group to an application with `okta_assign_group_to_app` (`app_id`, `group_id`). Verify `okta_list_app_groups` (`app_id`) lists the group.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| 401 or 403 from Okta | `OKTA_ORG_URL` or `OKTA_API_TOKEN` missing, expired or lacking admin scope | Set both variables with a token that has group and app admin rights, then call `okta_list_groups` to confirm access. |
| Destructive call refused | `okta_remove_group_member`, `okta_delete_group` or an unassign tool ran without `confirm=true` | Confirm the ids with the requester and call the tool again with `confirm=true`. |
| Rule assigns nobody | The new group rule is still INACTIVE | Call `okta_activate_group_rule` with the `rule_id` and check `okta_list_group_rules`. |

## Tools
| Tool | Purpose |
|------|---------|
| `okta_list_groups`, `okta_search_groups`, `okta_get_group` | Find and read groups |
| `okta_create_group`, `okta_update_group` | Create or rename a group |
| `okta_delete_group` | Delete a group (destructive) |
| `okta_list_group_members`, `okta_add_group_member` | Read or extend membership |
| `okta_remove_group_member` | Remove a member (destructive) |
| `okta_list_group_rules`, `okta_create_group_rule`, `okta_activate_group_rule` | Dynamic membership rules |
| `okta_deactivate_group_rule` | Deactivate a rule (destructive) |
| `okta_list_apps`, `okta_get_app`, `okta_create_app`, `okta_update_app`, `okta_activate_app` | Application integrations |
| `okta_deactivate_app` | Deactivate an application (destructive) |
| `okta_list_app_users`, `okta_assign_user_to_app` | User assignments |
| `okta_unassign_user_from_app` | Remove a user assignment (destructive) |
| `okta_list_app_groups`, `okta_assign_group_to_app` | Group assignments |
| `okta_unassign_group_from_app` | Remove a group assignment (destructive) |

Destructive tools refuse to run unless called with `confirm=true` or
the operator sets `SCION_ALLOW_DESTRUCTIVE=true`.

### Key parameters
- `group_id` / `app_id` — required for read, membership, and assignment tools.
- `user_id` — for `okta_add_group_member`, `okta_remove_group_member`, and the user assignment tools.
- `name` / `description` — for `okta_create_group`; `name`, `expression` and `assign_group_ids` for `okta_create_group_rule`.
- `rule_id` — for the rule activation tools.

## Recipes
Add a user to a group (`okta_add_group_member`): `group_id` = `00g1abc...`, `user_id` = `00u1xyz...`.

Create a dynamic group rule (`okta_create_group_rule`): `name` = `eng-auto`, `assign_group_ids` = `["00g1eng..."]`, `expression` = `user.department=="engineering"`; then `okta_activate_group_rule` with the returned `rule_id`.

Assign a group to an application (`okta_assign_group_to_app`): `app_id` = `0oa1app...`, `group_id` = `00g1eng...`.

## Gotchas
- Group `delete` and `remove_member`/`unassign_*` are effectively access-revoking —
  `delete` needs confirmation; verify the group is not app-linked first.
- A newly created **group rule** is INACTIVE until you call `activate_rule`; users are
  only assigned while the rule is ACTIVE.
- Dynamic-rule-managed membership cannot be edited by hand — `remove_member` on a
  rule-populated group is overwritten on the next rule evaluation.
- App `update` is a PUT (full replacement) — fetch with `get`, mutate, then send the
  whole representation back, or you will drop settings.
- Group/app list page sizes are capped (200/1000-per-call defaults); use `max_items`.

## Related
- `okta-user-lifecycle` — the identities that populate groups and app assignments.
- `okta-directory-ingestion` — mirror groups/apps into the knowledge graph.
- Okta Groups API: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Group/
- Okta Applications API: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Application/
