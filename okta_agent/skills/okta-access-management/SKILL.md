---
name: okta-access-management
skill_type: skill
description: >-
  Okta group and application access administration via the okta-agent MCP server
  — manage groups and their membership, dynamic group rules (Okta Expression
  Language), application integrations, and user/group-to-app assignments. Use
  when the agent must grant or revoke access by adding users to groups, wiring
  dynamic group rules, or assigning users/groups to SSO applications. Do NOT use
  for individual user lifecycle/credentials (okta-user-lifecycle) or KG mirroring
  (okta-directory-ingestion).
license: MIT
tags: [okta, groups, applications, access, sso, rbac, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# Okta Access Management

Domain-typed access to the Okta **Groups**, **Group Rules** and **Applications**
APIs for access administration — the join between identities and the resources
they can reach. Prefer the `okta_groups` and `okta_apps` action-routed tools.

## When to use
- Create/read/update/delete groups; list or change membership.
- Author dynamic **group rules** (Okta Expression Language) and activate/deactivate them.
- List/read/create/update application integrations and their lifecycle.
- Assign or unassign **users** and **groups** to/from applications.

## When NOT to use
- User profile CRUD, lifecycle, credentials, or MFA factors → `okta-user-lifecycle`.
- Sign-on / password / MFA-enroll **policies** → the `okta_policies` tool.
- Bulk mirroring of directory objects into the KG → `okta-directory-ingestion`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`okta-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `OKTA_ORG_URL` | ✅ | Org base URL, e.g. `https://acme.okta.com` |
| `OKTA_API_TOKEN` | ✅ | SSWS API token (or OAuth client creds) |
| `OKTA_ALLOW_DESTRUCTIVE` | optional | Default gate for destructive actions (e.g. group `delete`) |

## Tools & actions
Prefer the **condensed** tools; each takes `action` + a `params_json` **JSON string**.

| Condensed tool | Actions |
|----------------|---------|
| `okta_groups` | `list`, `search`, `get`, `create`, `update`, `delete`, `list_members`, `add_member`, `remove_member`, `list_rules`, `create_rule`, `activate_rule`, `deactivate_rule` |
| `okta_apps` | `list`, `get`, `create`, `update`, `activate`, `deactivate`, `list_users`, `assign_user`, `unassign_user`, `list_groups`, `assign_group`, `unassign_group` |

### Key parameters
- `group_id` / `app_id` — required for read, membership, and assignment actions.
- `user_id` — for `add_member`/`remove_member` and app `assign_user`/`unassign_user`.
- `name` / `description` — for group `create`; `expression` + `name` for `create_rule`.
- `rule_id` — for `activate_rule` / `deactivate_rule`.

## Recipes (`params_json`)
Add a user to a group:
```json
{"group_id":"00g1abc...","user_id":"00u1xyz..."}
```
Create a dynamic group rule (all users in the `engineering` department):
```json
{"name":"eng-auto","group_ids":["00g1eng..."],"expression":"user.department==\"engineering\""}
```
Assign a group to an application:
```json
{"app_id":"0oa1app...","group_id":"00g1eng..."}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
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
- Okta Groups API: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Group/
- Okta Applications API: https://developer.okta.com/docs/api/openapi/okta-management/management/tag/Application/
