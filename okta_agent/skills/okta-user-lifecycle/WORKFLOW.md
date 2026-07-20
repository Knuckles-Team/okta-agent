# Okta User Lifecycle

Okta user identity and lifecycle operations via the okta-agent MCP server — list/search users, read one by id or login, create/update profiles, and drive lifecycle transitions (activate, deactivate, suspend, unsuspend, unlock) plus credential actions (expire/reset password, clear sessions) and MFA factor reads. Use when the agent must provision, deprovision, or troubleshoot an Okta user, or read a user's groups/apps/factors. Do NOT use for group membership management (okta-access-management) or bulk KG mirroring (okta-directory-ingestion).

# Okta User Lifecycle

Domain-typed access to the Okta **Users** and **UserLifecycle** APIs for
provisioning, deprovisioning and credential/MFA troubleshooting. Prefer the
`okta_users` action-routed tool over raw HTTP — it carries the lifecycle state
machine and gates destructive actions.

## When to use
- List or search users (by `q` prefix or structured SCIM conditions).
- Read one user by id, login, or login shortname.
- Create or partially update a user profile / credentials.
- Drive lifecycle: `activate`, `deactivate`, `suspend`, `unsuspend`, `unlock`.
- Credential / session ops: `expire_password`, `reset_password`, `clear_sessions`.
- Read a user's `list_groups`, `list_apps`, `list_factors`.

## When NOT to use
- Adding/removing users to groups or assigning apps → `okta-access-management`.
- Creating groups, group rules, or application integrations → `okta-access-management`.
- Bulk mirroring users/groups/apps into the knowledge graph → `okta-directory-ingestion`.
- System Log / audit event queries → the `okta_system` tool.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`okta-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `OKTA_ORG_URL` | ✅ | Org base URL, e.g. `[configured-endpoint]` |
| `OKTA_API_TOKEN` | ✅ | SSWS API token (or OAuth client creds below) |
| `OKTA_CLIENT_ID` / `OKTA_PRIVATE_KEY` | optional | OAuth2 service-app auth |
| `OKTA_ALLOW_DESTRUCTIVE` | optional | Default gate for destructive actions |

## Tools & actions
Prefer the **condensed** tool; it takes `action` + a `params_json` **JSON string**.

| Condensed tool | Actions |
|----------------|---------|
| `okta_users` | `list`, `search`, `get`, `create`, `update`, `activate`, `deactivate`, `suspend`, `unsuspend`, `unlock`, `expire_password`, `reset_password`, `clear_sessions`, `list_groups`, `list_apps`, `list_factors` |

Destructive actions (`deactivate`, `suspend`, `expire_password`, `reset_password`,
`clear_sessions`) require `allow_destructive=true` (or `OKTA_ALLOW_DESTRUCTIVE=True`).

### Key parameters
- `user_id` — required for get/lifecycle/credential/related actions (accepts id, login, or login shortname).
- `profile` — object with at least `firstName`, `lastName`, `email`, `login` for `create`.
- `credentials`, `group_ids`, `activate` — optional on `create`.
- `send_email`, `temp_password`, `oauth_tokens` — optional flags on lifecycle/credential actions.

## Recipes (`params_json`)
List active users (structured search):
```json
{"conditions":[{"field":"status","op":"eq","value":"ACTIVE"}],"joiner":"and","limit":50}
```
Create + immediately activate a user:
```json
{"profile":{"firstName":"Ada","lastName":"Lovelace","email":"[REDACTED_EMAIL]","login":"[REDACTED_EMAIL]"},"activate":true}
```
Reset a password without emailing (returns a one-time reset URL) — destructive:
```json
{"user_id":"00u1abc...","send_email":false}
```
(with `allow_destructive=true`)

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- Lifecycle transitions are state-gated: `activate` needs STAGED/DEPROVISIONED;
  `unsuspend` needs SUSPENDED; `unlock` needs LOCKED_OUT — a wrong state returns an
  Okta error envelope, not success.
- `update` is a POST (partial merge); a full PUT-style replace is not exposed to
  avoid accidentally wiping profile attributes.
- `reset_password` with `send_email:false` returns a one-time `resetPasswordUrl`
  instead of mailing the user — treat it as a secret.
- Users list page size is capped at 200; use `max_items` for the overall cap and
  the returned `next_cursor` to resume.

## Related
- `okta-access-management` — groups, group rules, and app assignments.
- `okta-directory-ingestion` — mirror users/groups/apps into the knowledge graph.
- Okta Users API: [configured-endpoint]
