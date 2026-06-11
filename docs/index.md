# okta-agent

Okta **API + MCP Server + A2A Agent** for the agent-utilities ecosystem — a typed,
action-routed connector for the Okta Management API (users, groups, applications,
policies, and the system log).

!!! info "Official documentation"
    This site is the canonical reference for `okta-agent`, maintained alongside
    every release.

[![PyPI](https://img.shields.io/pypi/v/okta-agent)](https://pypi.org/project/okta-agent/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/okta-agent)](https://github.com/Knuckles-Team/okta-agent/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/okta-agent)

## Overview

`okta-agent` wraps the Okta Management API with typed, deterministic MCP tools and
an optional Pydantic-AI agent server. It provides:

- **`Api`** — a Python client (`okta_agent.api_client.Api`) composed from per-domain
  mixins. Raw `httpx`, no Okta SDK; every method documents the
  `developer.okta.com` endpoint it calls, captures the latest `X-Rate-Limit-*`
  snapshot, and backs off automatically on HTTP 429.
- **Action-routed MCP tools** — consolidated, togglable tool modules (`okta_users`,
  `okta_groups`, `okta_apps`, `okta_policies`, `okta_system`) that minimize token
  overhead in LLM contexts.
- **An A2A agent server** — a Pydantic-AI graph agent (console script `okta-agent`)
  that calls the MCP tool surface and exposes an AG-UI web interface.

Safety is built in: destructive operations (deactivate / delete / clear sessions /
password ops) are blocked unless explicitly allowed per call or via
`OKTA_ALLOW_DESTRUCTIVE`, and credential material is redacted from logs and error
envelopes.

`okta-agent` complements `keycloak-agent`: the same verb taxonomy over the
commercial IdP, so agents can switch identity providers without relearning tools.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP and agent servers, Docker Compose.
- :material-console: **[Usage](usage.md)** — the MCP tools, the `Api` client, and the CLI.
- :material-sitemap: **[Overview](overview.md)** — the action-routed tool surface and architecture.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:OKTA-*` registry.

</div>

## Quick start

```bash
pip install "okta-agent[mcp]"
okta-mcp                          # stdio MCP server (default transport)
```

Connect it to an Okta org:

```bash
export OKTA_ORG_URL=https://acme.okta.com
export OKTA_API_TOKEN=<api-token>
okta-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

See **[Installation](installation.md)** and **[Deployment](deployment.md)** for the
full matrix (PyPI extras, Docker image, all transports, the agent server).

!!! note "Backing platform"
    Okta is a managed SaaS identity platform — there is no self-hosted deployment
    recipe, so this site intentionally omits the *Backing Platform* page that
    connectors to self-hostable systems carry.
