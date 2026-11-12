# Okta User Lifecycle

Okta user identity and lifecycle operations via the okta-agent MCP server — list/search users, read one by id or login, create/update profiles, and drive lifecycle transitions (activate, deactivate, suspend, unsuspend, unlock) plus credential actions (expire/reset password, clear sessions) and MFA factor reads. Use when the agent must provision, deprovision, or troubleshoot an Okta user, or read a user's groups/apps/factors. Do NOT use for group membership management (okta-access-management) or bulk KG mirroring (okta-directory-ingestion).

# Okta User Lifecycle

Domain-typed access to the Okta **Users** and **UserLifecycle** APIs for
provisioning, deprovisioning and credential/MFA troubleshooting. Prefer the
typed `okta_*` user tools over raw HTTP — they carry the lifecycle state
machine and gate destructive operations.

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
- System Log / audit event queries → the `okta_get_system_log` tool.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`okta-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `OKTA_ORG_URL` | ✅ | Org base URL, e.g. `[configured-endpoint]` |
| `OKTA_API_TOKEN` | ✅ | SSWS API token (or OAuth client creds below) |
| `OKTA_CLIENT_ID` / `OKTA_PRIVATE_KEY` | optional | OAuth2 service-app auth |

## Tools
| Tool | Purpose |
|------|---------|
| `okta_list_users` | List users (`q` prefix, `filter_expr`, `search`) |
| `okta_search_users` | Structured SCIM search with `conditions` and `joiner` |
| `okta_get_user` | Read one user by id, login or login shortname |
| `okta_create_user` | Create a user (optionally activate and add to groups) |
| `okta_update_user` | Partially update a profile or credentials |
| `okta_activate_user` | Activate a STAGED or DEPROVISIONED user |
| `okta_deactivate_user` | Deprovision a user (destructive) |
| `okta_suspend_user` | Suspend an ACTIVE user (destructive) |
| `okta_unsuspend_user` | Return a SUSPENDED user to ACTIVE |
| `okta_unlock_user` | Unlock a LOCKED_OUT user |
| `okta_expire_password` | Expire a password, optionally with a temp password (destructive) |
| `okta_reset_password` | Start the password-reset flow (destructive) |
| `okta_clear_user_sessions` | Revoke all sessions, optionally OAuth tokens (destructive) |
| `okta_list_user_groups` | Groups a user belongs to |
| `okta_list_user_apps` | Applications assigned to a user |
| `okta_list_user_factors` | MFA factors enrolled by a user |

Destructive tools (`okta_deactivate_user`, `okta_suspend_user`, `okta_expire_password`,
`okta_reset_password`, `okta_clear_user_sessions`) refuse to run unless called with
`confirm=true` or the operator sets `SCION_ALLOW_DESTRUCTIVE=true`.

### Key parameters
- `user_id` — required for get, lifecycle, credential and related reads (accepts id, login, or login shortname).
- `profile` — object with at least `firstName`, `lastName`, `email`, `login` for `okta_create_user`.
- `credentials`, `group_ids`, `activate` — optional on `okta_create_user`.
- `send_email`, `temp_password`, `oauth_tokens` — optional flags on lifecycle and credential tools.

## Recipes
List active users (`okta_search_users`): `conditions` = `[{"field":"status","op":"eq","value":"ACTIVE"}]`, `joiner` = `and`, `limit` = 50.

Create and immediately activate a user (`okta_create_user`): `profile` = `{"firstName":"Ada","lastName":"Lovelace","email":"ada@acme.com","login":"ada@acme.com"}`, `activate` = true.

Reset a password without emailing (`okta_reset_password`, destructive): `user_id` = `00u1abc...`, `send_email` = false, `confirm` = true. The response carries a one-time reset URL.

## Gotchas
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
