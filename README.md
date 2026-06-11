# okta-agent

Enterprise CIAM/SSO connector for the agent fleet: a production-grade MCP
server and Pydantic AI agent over the **Okta Management API** — users, groups,
applications, policies, and the system log. Complements `keycloak-agent`
(open-source IdP) with the commercial-IdP side of the house, mirroring its
verb taxonomy so agents can switch IdPs with familiar verbs.

- Raw `httpx` client — no Okta SDK; every method documents the endpoint it calls.
- Two auth modes: **SSWS API token** and **OAuth2 private-key-JWT** (org
  authorization server, Okta API scopes).
- Rate-limit aware: every response envelope carries the latest
  `X-Rate-Limit-*` snapshot; HTTP 429 triggers capped automatic backoff.
- Cursor pagination via `Link: rel="next"` headers (Okta's `after` cursor),
  with hard item caps and resumable `next_cursor`s.
- Safety: destructive operations (deactivate / delete / clear sessions /
  password ops) are blocked unless explicitly allowed; credential material is
  redacted from logs and error envelopes.

## Install

```bash
pip install okta-agent            # core API client
pip install okta-agent[mcp]       # + MCP server
pip install okta-agent[agent]     # + Pydantic AI agent server
```

## Configure

```bash
export OKTA_ORG_URL="https://acme.okta.com"

# Mode 1 — SSWS API token (takes precedence)
export OKTA_API_TOKEN="<api token>"

# Mode 2 — OAuth2 private-key-JWT (service app, Okta API scopes)
export OKTA_CLIENT_ID="0oa..."
export OKTA_PRIVATE_KEY_FILE="/path/to/key.pem"   # or OKTA_PRIVATE_KEY inline
export OKTA_SCOPES="okta.users.read okta.groups.manage"
```

See `.env.example` for every knob (`OKTA_SSL_VERIFY`, `OKTA_MAX_RETRIES`,
`OKTA_BACKOFF_CAP_SECONDS`, `OKTA_ALLOW_DESTRUCTIVE`, per-tool switches).

## Run

```bash
okta-mcp                                  # stdio MCP server
okta-mcp --transport streamable-http --host 0.0.0.0 --port 8000
okta-agent                                # A2A agent server
```

## Tools

Five consolidated, action-routed tools. Each takes `action`, `params_json`,
and (where applicable) `allow_destructive`.

| Tool | Actions | Destructive (gated) |
|------|---------|---------------------|
| `okta_users` | list, search, get, create, update, activate, deactivate, suspend, unsuspend, unlock, expire_password, reset_password, list_groups, list_apps, list_factors, clear_sessions | deactivate, suspend, expire_password, reset_password, clear_sessions |
| `okta_groups` | list, search, get, create, update, delete, list_members, add_member, remove_member, list_rules, create_rule, activate_rule, deactivate_rule | delete, remove_member, deactivate_rule |
| `okta_apps` | list, get, create (oidc/saml/bookmark templates), update, activate, deactivate, list_users, assign_user, unassign_user, list_groups, assign_group, unassign_group | deactivate, unassign_user, unassign_group |
| `okta_policies` | list (okta_sign_on/password/mfa_enroll/access_policy), get, list_rules, activate, deactivate, activate_rule, deactivate_rule — *policy/rule create+update intentionally out of scope in this release* | deactivate, deactivate_rule |
| `okta_system` | org, list_authorization_servers, logs (since/until/filter/q, capped at 1000 events, resumable cursor), list_authenticators, list_factors, list_zones | — |

### Examples

```json
{"action": "search", "params_json": "{\"conditions\": [{\"field\": \"status\", \"op\": \"eq\", \"value\": \"ACTIVE\"}, {\"field\": \"profile.department\", \"op\": \"eq\", \"value\": \"Engineering\"}]}"}
```

```json
{"action": "create", "params_json": "{\"template\": \"oidc\", \"label\": \"My App\", \"settings\": {\"redirect_uris\": [\"https://app.example.com/cb\"]}}"}
```

```json
{"action": "deactivate", "params_json": "{\"user_id\": \"00u1\"}", "allow_destructive": true}
```

Every successful response is an envelope:

```json
{"data": [...], "rate_limit": {"limit": 600, "remaining": 599, "reset": 1700000000}, "count": 5, "truncated": false, "next_cursor": null}
```

Errors map Okta's envelope: `{"error": {"status", "error_code", "error_summary", "error_id", "error_causes", "rate_limit"}}`.

## Keycloak parity

Verbs intentionally mirror `keycloak-agent` where the concepts overlap, so an
agent fluent in one IdP connector can drive the other:

| Concept | keycloak-agent | okta-agent |
|---------|----------------|------------|
| Users CRUD | `keycloak_agent_users` list/get/create/update | `okta_users` list/get/create/update |
| Password reset | `reset_password` | `reset_password` (plus expire_password) |
| User's groups | `list_users_by_user_id_groups` | `list_groups` |
| Groups CRUD + members | `keycloak_agent_groups` | `okta_groups` (+ Okta group rules) |
| OAuth/SAML clients | `keycloak_agent_clients` | `okta_apps` (Keycloak "clients" = Okta "apps") |
| Auth policies/flows | `keycloak_agent_authentication` | `okta_policies` (read + lifecycle) |
| Server/org info & events | `keycloak_agent_info` / attack detection | `okta_system` (org + system log) |

Okta-only surface: lifecycle states (suspend/unlock), group rules, app
assignment profiles, network zones, Okta API scopes via private-key-JWT.

## Development

```bash
pip install -e .[mcp,test]
pytest -v
pre-commit run --all-files
```

API references are cited in every client docstring
(https://developer.okta.com/docs/api/).
