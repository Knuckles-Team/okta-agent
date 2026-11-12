# Okta Access Management

Okta group and application access administration via the okta-agent MCP server — manage groups and their membership, dynamic group rules (Okta Expression Language), application integrations, and user/group-to-app assignments. Use when the agent must grant or revoke access by adding users to groups, wiring dynamic group rules, or assigning users/groups to SSO applications. Do NOT use for individual user lifecycle/credentials (okta-user-lifecycle) or KG mirroring (okta-directory-ingestion).

# Okta Access Management

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
| `OKTA_ORG_URL` | ✅ | Org base URL, e.g. `[configured-endpoint]` |
| `OKTA_API_TOKEN` | ✅ | SSWS API token (or OAuth client creds) |
| `OKTA_ALLOW_DESTRUCTIVE` | optional | Default gate for destructive operations (e.g. `okta_delete_group`) |

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

Destructive tools refuse to run unless called with `allow_destructive=true` or
`OKTA_ALLOW_DESTRUCTIVE=True` is set.

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
  `delete` is gated by `allow_destructive`; verify the group is not app-linked first.
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
- Okta Groups API: [configured-endpoint]
- Okta Applications API: [configured-endpoint]
