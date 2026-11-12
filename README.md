# Okta Agent
## CLI or API | MCP

![PyPI - Version](https://img.shields.io/pypi/v/okta-agent)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/okta-agent)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/okta-agent)
![PyPI - License](https://img.shields.io/pypi/l/okta-agent)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/okta-agent)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/okta-agent)

> **Documentation** — Installation, deployment, usage across the API, CLI, and MCP
> server live on the docs site:
> <https://knuckles-team.github.io/okta-agent/>

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configure](#configure)
- [Environment Variables](#environment-variables)
- [Quick Start](#quick-start)
- [Run](#run)
- [MCP Tools](#mcp-tools)
- [Deployment](#deployment)
- [Keycloak Parity](#keycloak-parity)
- [Development](#development)

## Overview

Enterprise CIAM/SSO connector for the agent fleet: a production-grade MCP
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
- Safety: destructive operations (disable / remove / clear sessions /
  password ops) are blocked unless explicitly allowed; credential material is
  redacted from logs and error envelopes.

## Architecture

## Installation

> **Install the connector-focused `[mcp]` extra.** Examples use `okta-agent[mcp]` to add
> FastMCP / FastAPI through `scion-sdk`; the required Scion SDK core
> enables model orchestration.

Pick the extra that matches what the operator want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `okta-agent[mcp]` | Connector-focused MCP server (`scion-sdk` — FastMCP/FastAPI + `medulla`) | The operator only run the **MCP server** (smallest install / image) |
| `okta-agent[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

### Container images (`:mcp`)

One multi-stage `docker/Dockerfile` builds the MCP-only image (`--target mcp`):

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|

```bash
```

agent (`immutable agent digest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`medulla`)

Scion SDK core dependency (`medulla`). The `[mcp]` extra keeps
deployments can use the bundled engine. For production or shared state, run
**medulla as a dedicated database service** and configure the runtime to use it.
Deployment recipes (single-node + Raft HA), connection configuration, and architecture
diagrams are documented in the
[medulla deployment guide](https://knuckles-team.github.io/medulla/deployment/).

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

See `.env.example` for every knob (`OKTA_TLS_PROFILE`, `OKTA_MAX_RETRIES`,
`OKTA_BACKOFF_CAP_SECONDS`, `OKTA_ALLOW_DESTRUCTIVE`, per-tool switches).

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` |  |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | options: stdio, streamable-http, sse |
| `ENABLE_OTEL` | `True` |  |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:8080/api/public/otel` |  |
| `OTEL_EXPORTER_OTLP_PUBLIC_KEY_REF` | `secret://telemetry/otlp-public-key` |  |
| `OTEL_EXPORTER_OTLP_SECRET_KEY_REF` | `secret://telemetry/otlp-secret-key` |  |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` |  |
| `EUNOMIA_TYPE` | `none` | options: none, embedded, remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `EUNOMIA_REMOTE_URL` | `http://eunomia-server:8000` |  |
| `OKTA_ORG_URL` | `https://acme.okta.com` | Okta org URL (no trailing slash), e.g. https://acme.okta.com |
| `OKTA_AGENT_BASE_URL` | — | Accepted as a fallback for OKTA_ORG_URL when that is unset |
| `OKTA_API_TOKEN` | secret-injected |  |
| `OKTA_CLIENT_ID` | — | Service-app client id (org authorization server, client_credentials grant) |
| `OKTA_PRIVATE_KEY` | secret-injected | PEM private key inline, or a path to a PEM file |
| `OKTA_PRIVATE_KEY_FILE` | secret-injected |  |
| `OKTA_KEY_ID` | secret-injected | Optional JWKS key id for the client assertion header |
| `OKTA_SCOPES` | `okta.users.read okta.groups.read okta.apps.read` | Space-separated Okta API scopes |
| `OKTA_TLS_PROFILE` | `system` | Named outbound TLS policy. Configure profiles in AgentConfig; a reference may resolve runtime trust material without persisting certificate paths here. |
| `OKTA_TLS_PROFILE_REF` | — |  |
| `OKTA_MAX_RETRIES` | `2` | 429 handling: retry attempts and backoff cap (seconds) |
| `OKTA_BACKOFF_CAP_SECONDS` | `60` |  |
| `OKTA_ALLOW_DESTRUCTIVE` | `False` | Safety: org-wide default for destructive tool actions (deactivate/delete/clear-sessions/password ops). Per-call allow_destructive=true also works; default is blocked. |
| `USERSTOOL` | `True` | Tool registration switches |
| `GROUPSTOOL` | `True` |  |
| `APPSTOOL` | `True` |  |
| `POLICIESTOOL` | `True` |  |
| `SYSTEMTOOL` | `True` |  |
| `INGESTTOOL` | `True` |  |

#### Inherited scion-sdk variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_TOOL_MODE` | `intent` | Tool surface: `intent` \| `condensed` \| `verbose` \| `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |

_30 package + 16 inherited variable(s). Auto-generated from `.env.example` + the shared scion-sdk set — do not edit._
<!-- ENV-VARS-TABLE:END -->

| Variable | Default | Purpose |
|----------|---------|---------|
| `OKTA_ORG_URL` | — | Okta org URL, no trailing slash (`OKTA_AGENT_BASE_URL` accepted as fallback) |
| `OKTA_API_TOKEN` | — | SSWS API token (auth mode 1, takes precedence) |
| `OKTA_CLIENT_ID` | — | Service-app client id (private-key-JWT) |
| `OKTA_PRIVATE_KEY` / `OKTA_PRIVATE_KEY_FILE` | — | PEM private key inline or path |
| `OKTA_KEY_ID` | — | Optional JWKS key id for the client assertion |
| `OKTA_SCOPES` | read scopes | Space-separated Okta API scopes |
| `OKTA_TLS_PROFILE` | `system` | Named outbound TLS policy from AgentConfig |
| `OKTA_MAX_RETRIES` | `2` | 429 retry attempts |
| `OKTA_BACKOFF_CAP_SECONDS` | `60` | 429 backoff cap |
| `OKTA_ALLOW_DESTRUCTIVE` | `False` | Org-wide default for destructive tool actions |
| `HOST` / `PORT` / `TRANSPORT` | `0.0.0.0` / `8000` / `stdio` | MCP server bind + transport |
| `USERSTOOL` / `GROUPSTOOL` / `APPSTOOL` / `POLICIESTOOL` / `SYSTEMTOOL` | `True` | Per-domain tool toggles |
| `ENABLE_OTEL` / `OTEL_EXPORTER_OTLP_*` | — | Telemetry (OTEL / Langfuse) |
| `EUNOMIA_TYPE` / `EUNOMIA_POLICY_FILE` / `EUNOMIA_REMOTE_URL` | `none` | MCP authorization middleware |
| `AUTH_TYPE` | `none` | MCP server auth mode (Docker) |

## Quick Start

```python
from okta_agent import Api
from okta_agent.api.credentials import SswsToken

api = Api(org_url="https://acme.okta.com", credential=SswsToken("<token>"))

active = api.search_users(
    conditions=[{"field": "status", "op": "eq", "value": "ACTIVE"}],
)
print(active["data"], active["rate_limit"])

# Or build typed tool params for the MCP surface:
params = SearchInput(
    conditions=[FilterCondition(field="status", op="eq", value="ACTIVE")]
).model_dump_json(exclude_none=True)
```

## Run

```bash
okta-mcp                                  # stdio MCP server
okta-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## MCP Tools

One typed tool per Okta operation, named `okta_<operation>` (`okta_list_users`, `okta_create_group`, `okta_get_system_log`, ...), plus four graph-ingest tools. No tool takes an `action`. Destructive operations (deactivate, suspend, delete, remove, expire or reset password, clear sessions) take `allow_destructive` and refuse to run unless it is true or `OKTA_ALLOW_DESTRUCTIVE` is set.

| Area | Tools |
|------|-------|
| Users | `okta_list_users`, `okta_search_users`, `okta_get_user`, `okta_create_user`, `okta_update_user`, `okta_activate_user`, `okta_deactivate_user`*, `okta_suspend_user`*, `okta_unsuspend_user`, `okta_unlock_user`, `okta_expire_password`*, `okta_reset_password`*, `okta_clear_user_sessions`*, `okta_list_user_groups`, `okta_list_user_apps`, `okta_list_user_factors` |
| Groups | `okta_list_groups`, `okta_search_groups`, `okta_get_group`, `okta_create_group`, `okta_update_group`, `okta_delete_group`*, `okta_list_group_members`, `okta_add_group_member`, `okta_remove_group_member`*, `okta_list_group_rules`, `okta_create_group_rule`, `okta_activate_group_rule`, `okta_deactivate_group_rule`* |
| Applications | `okta_list_apps`, `okta_get_app`, `okta_create_app`, `okta_update_app`, `okta_activate_app`, `okta_deactivate_app`*, `okta_list_app_users`, `okta_assign_user_to_app`, `okta_unassign_user_from_app`*, `okta_list_app_groups`, `okta_assign_group_to_app`, `okta_unassign_group_from_app`* |
| Policies | `okta_list_policies`, `okta_get_policy`, `okta_list_policy_rules`, `okta_activate_policy`, `okta_deactivate_policy`*, `okta_activate_policy_rule`, `okta_deactivate_policy_rule`* |
| Org and audit | `okta_get_org`, `okta_list_authorization_servers`, `okta_get_system_log`, `okta_list_authenticators`, `okta_list_org_factors`, `okta_list_network_zones` |
| Graph | `okta_ingest_users`, `okta_ingest_groups`, `okta_ingest_apps`, `okta_ingest_all` |

`*` destructive.


### Examples

Search users (`okta_search_users`): `conditions` = `[{"field": "status", "op": "eq", "value": "ACTIVE"}, {"field": "profile.department", "op": "eq", "value": "Engineering"}]`.

Create an OIDC app (`okta_create_app`): `template` = `oidc`, `label` = `My App`, `settings` = `{"redirect_uris": ["https://app.example.com/cb"]}`.

Deactivate a user (`okta_deactivate_user`): `user_id` = `00u1`, `allow_destructive` = true.

Every successful response is an envelope:

```json
{"data": [...], "rate_limit": {"limit": 600, "remaining": 599, "reset": 1700000000}, "count": 5, "truncated": false, "next_cursor": null}
```

Errors map Okta's envelope: `{"error": {"status", "error_code", "error_summary", "error_id", "error_causes", "rate_limit"}}`.

## Deployment

`MCP_URL`, `PROVIDER`, and `MODEL_ID` from the environment. Prebuilt images:
(full agent) — see [Container images](#container-images-mcp-vs-agent). See
[docs/deployment.md](docs/deployment.md) for transports, reverse proxy, and DNS
guidance.

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`okta-agent` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/okta-agent/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Keycloak parity

Verbs intentionally mirror `keycloak-agent` where the concepts overlap, so an
agent fluent in one IdP connector can drive the other:

| Concept | keycloak-agent | okta-agent |
|---------|----------------|------------|
| Users CRUD | `keycloak_agent_users` list/get/create/update | `okta_list_users` / `okta_get_user` / `okta_create_user` / `okta_update_user` |
| Password reset | `reset_password` | `reset_password` (plus expire_password) |
| User's groups | `list_users_by_user_id_groups` | `list_groups` |
| Groups CRUD + members | `keycloak_agent_groups` | `okta_list_groups` (+ Okta group rules) |
| OAuth/SAML clients | `keycloak_agent_clients` | `okta_list_apps` (Keycloak "clients" = Okta "apps") |
| Auth policies/flows | `keycloak_agent_authentication` | `okta_list_policies` (read + lifecycle) |
| Server/org info & events | `keycloak_agent_info` / attack detection | `okta_get_org` / `okta_get_system_log` |

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

<!-- BEGIN scion-sdk-deployment (generated; do not edit between markers) -->

## Deploy with `scion-sdk-deployment`

Provision this package with the consolidated **`scion-sdk-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `okta-agent` with scion-sdk-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "okta-agent[mcp]"`, then run `okta-mcp` |
| Immutable container | deploy `registry.example.invalid/okta-agent@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END scion-sdk-deployment -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, Arbora delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
