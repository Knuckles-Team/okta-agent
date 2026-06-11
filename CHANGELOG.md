# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
