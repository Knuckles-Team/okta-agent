# Okta Agent
## CLI or API | MCP | Agent

![PyPI - Version](https://img.shields.io/pypi/v/okta-agent)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/okta-agent)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/okta-agent)
![PyPI - License](https://img.shields.io/pypi/l/okta-agent)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/okta-agent)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/okta-agent)

*Version: 1.0.1*

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

## Architecture

```mermaid
graph TD
    User([User/A2A]) --> Server[A2A Server / okta-agent]
    Server --> Agent[Pydantic AI Agent]
    Agent --> MCP[MCP Server / okta-mcp]
    MCP --> Client[Api facade / httpx]
    Client --> ExternalAPI([Okta Management API])
```

## Installation

> **Install the slim `[mcp]` extra.** For MCP-server hosting (including `uvx` /
> container deploys), install `okta-agent[mcp]` — the MCP-server extra that pulls
> only the FastMCP / FastAPI tooling (`agent-utilities[mcp]`). It deliberately
> **excludes** the heavy agent runtime (the epistemic-graph engine, `pydantic-ai`,
> `dspy`, `llama-index`, `tree-sitter`), so installs are dramatically smaller and
> faster. Use the full `[agent]` extra only when you need the integrated Pydantic
> AI agent.

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `okta-agent[mcp]` | Slim MCP server only (`agent-utilities[mcp]` — FastMCP/FastAPI) | You only run the **MCP server** (smallest install / image) |
| `okta-agent[agent]` | Full agent runtime (`agent-utilities[agent,logfire]` — Pydantic AI + the epistemic-graph engine) | You run the **integrated A2A agent** |
| `okta-agent[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
pip install okta-agent            # core API client
pip install okta-agent[mcp]       # slim MCP server (FastMCP/FastAPI)
pip install okta-agent[agent]     # full A2A agent runtime + epistemic-graph engine
pip install okta-agent[all]       # everything (development)
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `knucklessg1/okta-agent:mcp` | `--target mcp` | `okta-agent[mcp]` — **slim**, no engine/`pydantic-ai`/`dspy`/`llama-index`/`tree-sitter` | `okta-mcp` |
| `knucklessg1/okta-agent:latest` | `--target agent` (default) | `okta-agent[agent]` — **full** agent runtime + epistemic-graph engine | `okta-agent` |

```bash
docker build --target mcp   -t knucklessg1/okta-agent:mcp    docker/   # slim MCP server
docker build --target agent -t knucklessg1/okta-agent:latest docker/   # full agent
```

`docker/mcp.compose.yml` runs the slim `:mcp` server; `docker/agent.compose.yml` runs the
agent (`:latest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

The **full agent** (`[agent]` / `:latest`) embeds the **epistemic-graph** engine (pulled in
transitively via `agent-utilities[agent]`). For production — or to share one knowledge graph
across multiple agents — run **epistemic-graph as its own database container** and point the
agent at it instead of embedding it. Deployment recipes (single-node + Raft HA), connection
config, and the full database architecture (with diagrams) are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).
The slim `[mcp]` server does **not** require the database.

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
| `OTEL_EXPORTER_OTLP_PUBLIC_KEY` | `pk-...` |  |
| `OTEL_EXPORTER_OTLP_SECRET_KEY` | `sk-...` |  |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` |  |
| `EUNOMIA_TYPE` | `none` | options: none, embedded, remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `EUNOMIA_REMOTE_URL` | `http://eunomia-server:8000` |  |
| `OKTA_ORG_URL` | `https://acme.okta.com` | Okta org URL (no trailing slash), e.g. https://acme.okta.com |
| `OKTA_AGENT_BASE_URL` | — | Accepted as a fallback for OKTA_ORG_URL when that is unset |
| `OKTA_API_TOKEN` | — |  |
| `OKTA_CLIENT_ID` | — | Service-app client id (org authorization server, client_credentials grant) |
| `OKTA_PRIVATE_KEY` | — | PEM private key inline, or a path to a PEM file |
| `OKTA_PRIVATE_KEY_FILE` | — |  |
| `OKTA_KEY_ID` | — | Optional JWKS key id for the client assertion header |
| `OKTA_SCOPES` | `okta.users.read okta.groups.read okta.apps.read` | Space-separated Okta API scopes |
| `OKTA_SSL_VERIFY` | `True` | TLS verification toward the org |
| `OKTA_MAX_RETRIES` | `2` | 429 handling: retry attempts and backoff cap (seconds) |
| `OKTA_BACKOFF_CAP_SECONDS` | `60` |  |
| `OKTA_ALLOW_DESTRUCTIVE` | `False` | allow_destructive=true also works; default is blocked. |
| `USERSTOOL` | `True` | Tool registration switches |
| `GROUPSTOOL` | `True` |  |
| `APPSTOOL` | `True` |  |
| `POLICIESTOOL` | `True` |  |
| `SYSTEMTOOL` | `True` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_TOOL_MODE` | `condensed` | Tool surface: `condensed` | `verbose` | `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `MCP_CLIENT_AUTH` | — | Outbound MCP auth (`oidc-client-credentials` for fleet calls) |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET` | — | OIDC client secret (service-account auth) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_28 package + 14 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


| Variable | Default | Purpose |
|----------|---------|---------|
| `OKTA_ORG_URL` | — | Okta org URL, no trailing slash (`OKTA_AGENT_BASE_URL` accepted as fallback) |
| `OKTA_API_TOKEN` | — | SSWS API token (auth mode 1, takes precedence) |
| `OKTA_CLIENT_ID` | — | Service-app client id (private-key-JWT) |
| `OKTA_PRIVATE_KEY` / `OKTA_PRIVATE_KEY_FILE` | — | PEM private key inline or path |
| `OKTA_KEY_ID` | — | Optional JWKS key id for the client assertion |
| `OKTA_SCOPES` | read scopes | Space-separated Okta API scopes |
| `OKTA_SSL_VERIFY` | `True` | TLS verification toward the org |
| `OKTA_MAX_RETRIES` | `2` | 429 retry attempts |
| `OKTA_BACKOFF_CAP_SECONDS` | `60` | 429 backoff cap |
| `OKTA_ALLOW_DESTRUCTIVE` | `False` | Org-wide default for destructive tool actions |
| `HOST` / `PORT` / `TRANSPORT` | `0.0.0.0` / `8000` / `stdio` | MCP server bind + transport |
| `USERSTOOL` / `GROUPSTOOL` / `APPSTOOL` / `POLICIESTOOL` / `SYSTEMTOOL` | `True` | Per-domain tool toggles |
| `ENABLE_OTEL` / `OTEL_EXPORTER_OTLP_*` | — | Telemetry (OTEL / Langfuse) |
| `EUNOMIA_TYPE` / `EUNOMIA_POLICY_FILE` / `EUNOMIA_REMOTE_URL` | `none` | MCP authorization middleware |
| `AUTH_TYPE` | `none` | MCP server auth mode (Docker) |
| `DEFAULT_AGENT_NAME` / `AGENT_DESCRIPTION` / `AGENT_SYSTEM_PROMPT` | identity files | A2A agent identity overrides |

## Quick Start

```python
from okta_agent import Api
from okta_agent.api.credentials import SswsToken
from okta_agent.okta_input_models import SearchInput, FilterCondition

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
okta-agent                                # A2A agent server
```

## MCP Tools

Five consolidated, action-routed tools. Each takes `action`, `params_json`,
and (where applicable) `allow_destructive`.

<!-- This table is auto-generated by `python -m agent_utilities.mcp.readme_tools` — do not edit by hand. -->

<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (default — `MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `okta_apps` | `APPSTOOL` | Manage Okta applications — CRUD, lifecycle, and user/group assignments. |
| `okta_groups` | `GROUPSTOOL` | Manage Okta groups — CRUD, membership, and dynamic group rules. |
| `okta_policies` | `POLICIESTOOL` | Inspect Okta policies and toggle policy/rule lifecycle. |
| `okta_system` | `SYSTEMTOOL` | Inspect the Okta org — settings, auth servers, system log, authenticators, zones. |
| `okta_users` | `USERSTOOL` | Manage Okta users — lifecycle, credentials, groups/apps/factors, sessions. |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>54 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `okta_activate_app` | `APITOOL` | Activate an application. |
| `okta_activate_group_rule` | `APITOOL` | Activate a group rule. |
| `okta_activate_policy` | `APITOOL` | Activate a policy. |
| `okta_activate_policy_rule` | `APITOOL` | Activate a policy rule. |
| `okta_activate_user` | `APITOOL` | Activate a STAGED/DEPROVISIONED user. |
| `okta_add_group_member` | `APITOOL` | Add a user to a group. |
| `okta_assign_group_to_app` | `APITOOL` | Assign a group to an app. |
| `okta_assign_user_to_app` | `APITOOL` | Assign a user to an app with an optional app-specific profile. |
| `okta_clear_user_sessions` | `APITOOL` | Revoke all of a user's sessions — destructive. |
| `okta_create_app` | `APITOOL` | Create an app from a basic template (``oidc``/``saml``/``bookmark``). |
| `okta_create_group` | `APITOOL` | Create an OKTA_GROUP. |
| `okta_create_group_rule` | `APITOOL` | Create an INACTIVE group rule from an Okta Expression Language condition. |
| `okta_create_user` | `APITOOL` | Create a user, optionally activated immediately. |
| `okta_deactivate_app` | `APITOOL` | Deactivate an application — destructive. |
| `okta_deactivate_group_rule` | `APITOOL` | Deactivate a group rule — destructive. |
| `okta_deactivate_policy` | `APITOOL` | Deactivate a policy — destructive. |
| `okta_deactivate_policy_rule` | `APITOOL` | Deactivate a policy rule — destructive. |
| `okta_deactivate_user` | `APITOOL` | Deactivate (deprovision) a user — destructive. |
| `okta_delete_group` | `APITOOL` | Delete a group — destructive. |
| `okta_expire_password` | `APITOOL` | Expire a user's password — destructive. |
| `okta_get_app` | `APITOOL` | Get one application by id. |
| `okta_get_group` | `APITOOL` | Get one group by id. |
| `okta_get_org` | `APITOOL` | Get the org settings (company info, subdomain, status). |
| `okta_get_policy` | `APITOOL` | Get one policy, optionally expanded with its rules. |
| `okta_get_system_log` | `APITOOL` | Query the system log (audit events), capped and cursor-paginated. |
| `okta_get_user` | `APITOOL` | Get one user by id, login, or login shortname. |
| `okta_list_app_groups` | `APITOOL` | List the groups assigned to an app. |
| `okta_list_app_users` | `APITOOL` | List the users assigned to an app. |
| `okta_list_apps` | `APITOOL` | List applications with optional ``q`` label match or SCIM ``filter``. |
| `okta_list_authenticators` | `APITOOL` | List the org's authenticators (Okta Verify, WebAuthn, password, ...). |
| `okta_list_authorization_servers` | `APITOOL` | List custom authorization servers. |
| `okta_list_group_members` | `APITOOL` | List the users in a group. |
| `okta_list_group_rules` | `APITOOL` | List group rules. |
| `okta_list_groups` | `APITOOL` | List groups with optional ``q`` name prefix, SCIM ``filter`` or ``search``. |
| `okta_list_network_zones` | `APITOOL` | List network zones. |
| `okta_list_org_factors` | `APITOOL` | List org-level MFA factor enablement (legacy Factors API view). |
| `okta_list_policies` | `APITOOL` | List policies of one type (``okta_sign_on``/``password``/``mfa_enroll``/``access_policy``). |
| `okta_list_policy_rules` | `APITOOL` | List the rules of a policy. |
| `okta_list_user_apps` | `APITOOL` | List the app links assigned to a user. |
| `okta_list_user_factors` | `APITOOL` | List the enrolled MFA factors for a user. |
| `okta_list_user_groups` | `APITOOL` | List the groups a user belongs to. |
| `okta_list_users` | `APITOOL` | List users with optional ``q`` prefix match, SCIM ``filter`` or ``search``. |
| `okta_remove_group_member` | `APITOOL` | Remove a user from a group — destructive. |
| `okta_reset_password` | `APITOOL` | Start the password-reset flow — destructive. |
| `okta_search_groups` | `APITOOL` | Search groups from structured SCIM conditions (built safely). |
| `okta_search_users` | `APITOOL` | Search users from structured SCIM conditions (built safely). |
| `okta_suspend_user` | `APITOOL` | Suspend an ACTIVE user — destructive. |
| `okta_unassign_group_from_app` | `APITOOL` | Remove a group's app assignment — destructive. |
| `okta_unassign_user_from_app` | `APITOOL` | Remove a user's app assignment — destructive. |
| `okta_unlock_user` | `APITOOL` | Unlock a LOCKED_OUT user. |
| `okta_unsuspend_user` | `APITOOL` | Return a SUSPENDED user to ACTIVE. |
| `okta_update_app` | `APITOOL` | Replace an application (PUT semantics — pass the full app object). |
| `okta_update_group` | `APITOOL` | Replace a group's profile (PUT semantics — name is required). |
| `okta_update_user` | `APITOOL` | Partially update a user's profile and/or credentials. |

</details>

_5 action-routed tool(s) (default) · 54 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (`condensed` default · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

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

## Deployment

```bash
# MCP server only (port 8000, streamable-http, /health)
docker compose -f docker/mcp.compose.yml up -d

# MCP server + A2A agent server (agent on port 9021, AG-UI web interface)
docker compose -f docker/agent.compose.yml up -d
```

The A2A agent server (`okta-agent` console script, `agent_server.py`) reads
`MCP_URL`, `PROVIDER`, and `MODEL_ID` from the environment. Prebuilt images:
`knucklessg1/okta-agent:mcp` (slim MCP server) and `knucklessg1/okta-agent:latest`
(full agent) — see [Container images](#container-images-mcp-vs-agent). See
[docs/deployment.md](docs/deployment.md) for transports, reverse proxy, and DNS
guidance.

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`okta-agent` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/okta-agent/deployment/) has full, copy-paste
`mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://okta-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

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


<!-- BEGIN agent-os-genesis-deploy (generated; do not edit between markers) -->

## Deploy with `agent-os-genesis`

This package can be provisioned for you — skill-guided — by the **`agent-os-genesis`**
universal skill (its *single-package deploy mode*): it picks your install method, seeds
secrets to OpenBao/Vault (or `.env`), trusts your enterprise CA, registers the MCP
server, and verifies it — the same machinery that stands up the whole Agent OS, narrowed
to just this package. Ask your agent to **"deploy `okta-agent` with agent-os-genesis"**.

| Install mode | Command |
|------|---------|
| Bare-metal, prod (PyPI) | `uvx okta-mcp` · or `uv tool install okta-agent` |
| Bare-metal, dev (editable) | `uv pip install -e ".[all]"` · or `pip install -e ".[all]"` |
| Container, prod | deploy `knucklessg1/okta-agent:latest` via docker-compose / swarm / podman / podman-compose / kubernetes |
| Container, dev (editable) | deploy `docker/compose.dev.yml` (source-mounted at `/src`; edits live on restart) |

Secrets are read-existing + seeded via `vault_sync` — you are only prompted for what's missing.

<!-- END agent-os-genesis-deploy -->
