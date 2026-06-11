# Changelog

## 0.1.0 (2026-06-11)

Initial release — enterprise CIAM/SSO connector for the agent fleet.

- Raw httpx client for the Okta Management API (no Okta SDK), endpoint
  references cited in every method docstring.
- Auth: SSWS API token and OAuth2 private-key-JWT (org authorization server,
  Okta API scopes) with token caching/refresh.
- Rate-limit awareness: `X-Rate-Limit-*` snapshots in every response
  envelope; capped automatic backoff on HTTP 429.
- Cursor pagination via `Link: rel="next"` headers with item caps and
  resumable `next_cursor`.
- Five action-routed MCP tools: `okta_users`, `okta_groups`, `okta_apps`,
  `okta_policies` (read + lifecycle only), `okta_system` (capped system log).
- Safety: destructive operations gated behind `allow_destructive`
  (default false) / `OKTA_ALLOW_DESTRUCTIVE`; credential redaction in logs
  and error envelopes.
- SCIM filter builder with value escaping.
- Mocked-httpx test suite (no live Okta calls).
