# Concept Registry — Okta MCP

> **Prefix**: `CONCEPT:OKTA-*`
> **Bridge**: `CONCEPT:AU-ECO.messaging.native-backend-abstraction` (Unified Toolkit Ingestion)

## Project-Specific Concepts

| Concept ID | Name | Description |
|------------|------|-------------|
| `CONCEPT:OK-OS.governance.okta` | Core API Client Operations | Raw httpx client for the Okta Management API — rate-limit header tracking, capped 429 backoff, Link-header cursor pagination, error-envelope mapping |
| `CONCEPT:OK-OS.identity.okta` | Credential Strategies | SSWS API token and OAuth2 private-key-JWT (org authorization server, Okta API scopes) credential loading and rotation |
| `CONCEPT:OK-OS.governance.okta-2` | FastMCP Tools Execution | Action-routed MCP tools (users/groups/apps/policies/system) as thin shims over the API client |
| `CONCEPT:OK-OS.identity.default` | Safety Gating & Redaction | Destructive operations blocked behind `allow_destructive` (default false); credential material redacted from logs and error envelopes |
| `CONCEPT:OK-OS.governance.okta-3` | SCIM Filter Building | Structured, escaped construction of Okta's SCIM-style `filter` expressions |
| `CONCEPT:AU-ECO.messaging.native-backend-abstraction` | Ecosystem Compliance | Multi-package integration compliance standard |
