# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-11-12

### Changed
- The thirteen destructive operations now use the SDK's one declaration and guard (`destructive_operation`, scion-sdk 0.10.2). Each served tool carries the MCP `destructiveHint` and the SDK's `confirm` argument, and a call without confirmation sends no request to the org.

### Removed
- The connector's own gate: the per-call `allow_destructive` argument, the `OKTA_ALLOW_DESTRUCTIVE` setting, `allow_destructive_default`, `DestructiveBlockedError` and `_require_destructive`. For unattended use the one operator setting is `SCION_ALLOW_DESTRUCTIVE`.

## [2.3.9] - 2026-11-12

### Removed
- The five action-routed tool modules (`okta_users`, `okta_groups`, `okta_apps`, `okta_policies`, `okta_system`), the action-routed `okta_ingest` tool, and the `okta_input_models` module that mirrored their `params_json` payloads. Every action is a typed per-operation tool (`okta_list_users`, `okta_create_group`, `okta_get_system_log`, ...); the ingest is now four typed tools: `okta_ingest_users`, `okta_ingest_groups`, `okta_ingest_apps`, `okta_ingest_all`.

### Changed
- The destructive-operation gate moved from the action routers into the client. The thirteen destructive operations (`okta_deactivate_user`, `okta_suspend_user`, `okta_expire_password`, `okta_reset_password`, `okta_clear_user_sessions`, `okta_delete_group`, `okta_remove_group_member`, `okta_deactivate_group_rule`, `okta_deactivate_app`, `okta_unassign_user_from_app`, `okta_unassign_group_from_app`, `okta_deactivate_policy`, `okta_deactivate_policy_rule`) now take `allow_destructive` and refuse to run unless it is true or `OKTA_ALLOW_DESTRUCTIVE` is on. Before this change the typed tools were not gated.
- Connector surface: tool-use contracts, links, data locations, business roles, an operator prompt and three business-role prompts, ontology classes rooted in core classes, skills rewritten for the typed tools, scion-sdk 0.9.

## [2.3.8] - 2026-10-30

### Changed
- Require `scion-sdk>=0.6.4,<0.7.0`; `uv.lock` relocked.

## [2.3.6] - 2026-10-26

### Added
- Standard spec-delivery dashboard publication and the okta-agent development
  skill with the rapid-delivery contract.

## [2.3.5] - 2026-10-24

### Changed
- Central connector migration: requires `agent-connector-sdk>=0.5.4`; server bootstrap, version, containers, ontology artifacts, security scaffold and pre-commit config are provided centrally.

## [Unreleased]
### Added
- Golden-parity standardization (gitlab-api standard): full pre-commit hook
  set (mypy/vulture/bandit/codespell/hadolint/compose checks/repo validators),
  validation scripts (`security_sanitizer`, `verify_api_integration`,
  `validate_a2a_agent`, `validate_agent`), docker quartet (`debug.Dockerfile`,
  `mcp.compose.yml`, `agent.compose.yml`, `starship.toml`), `a2a.json`,
  `opencode.json`, root `mcp_config.json`, `MANIFEST.in`, `uv.lock`,
  `main_agent.json` (replacing `prompts/main_agent.md`), and a
  `docs/deployment.md` covering all transports, Compose, and Caddy/Technitium.
- Typed tool-input and response-envelope contracts in `okta_input_models.py` /
  `okta_response_models.py` (exported from the package root) with model tests.

### Changed
- `pyproject.toml` aligned to the golden shape (self-referencing `all` extra,
  vulture config); `.bumpversion.cfg` now syncs README, Dockerfile pin, and
  both server `__version__` strings.

## [0.1.0] - 2026-06-11

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
