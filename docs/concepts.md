# Concept Registry — Okta MCP

> **Prefix**: `CONCEPT:OKTA-*`
> **Bridge**: `CONCEPT:ECO-4.0` (Unified Toolkit Ingestion)

## Project-Specific Concepts

| Concept ID | Name | Description |
|------------|------|-------------|
| `CONCEPT:OKTA-1.1` | Core API Client Operations | Raw httpx client for the Okta Management API — rate-limit header tracking, capped 429 backoff, Link-header cursor pagination, error-envelope mapping |
| `CONCEPT:OKTA-1.2` | Credential Strategies | SSWS API token and OAuth2 private-key-JWT (org authorization server, Okta API scopes) credential loading and rotation |
| `CONCEPT:OKTA-1.3` | FastMCP Tools Execution | Action-routed MCP tools (users/groups/apps/policies/system) as thin shims over the API client |
| `CONCEPT:OKTA-1.4` | Safety Gating & Redaction | Destructive operations blocked behind `allow_destructive` (default false); credential material redacted from logs and error envelopes |
| `CONCEPT:OKTA-1.5` | SCIM Filter Building | Structured, escaped construction of Okta's SCIM-style `filter` expressions |
| `CONCEPT:ECO-4.0` | Ecosystem Compliance | Multi-package integration compliance standard |
