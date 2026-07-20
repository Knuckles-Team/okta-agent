# Installation

```bash
pip install okta-agent            # core API client
pip install okta-agent[mcp]       # + MCP server (okta-mcp)
pip install okta-agent[agent]     # + Pydantic AI agent server (okta-agent)
pip install okta-agent[all]       # everything
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `OKTA_ORG_URL` | `https://localhost` | Okta org base URL, e.g. `https://acme.okta.com` |
| `OKTA_API_TOKEN` | — | SSWS API token (auth mode 1; takes precedence) |
| `OKTA_CLIENT_ID` | — | Service-app client id (auth mode 2) |
| `OKTA_PRIVATE_KEY` / `OKTA_PRIVATE_KEY_FILE` | — | RS256 private key (PEM inline / path) |
| `OKTA_KEY_ID` | — | Optional `kid` for the client assertion |
| `OKTA_SCOPES` | `okta.users.read okta.groups.read okta.apps.read` | Space-separated Okta API scopes |
| `OKTA_TLS_PROFILE` | `system` | TLS verification |
| `OKTA_MAX_RETRIES` | `2` | Retry attempts on HTTP 429 |
| `OKTA_BACKOFF_CAP_SECONDS` | `60` | Upper bound on a single 429 backoff sleep |
| `OKTA_ALLOW_DESTRUCTIVE` | `False` | Org-wide default for the destructive-action gate |
| `USERSTOOL` … `SYSTEMTOOL` | `True` | Per-tool registration switches |

## Okta-side setup

- **SSWS token**: Admin Console → Security → API → Tokens
  (https://developer.okta.com/docs/guides/create-an-api-token/main/).
- **Private-key-JWT**: create an API Services app, grant Okta API scopes, and
  register the public key
  (https://developer.okta.com/docs/guides/implement-oauth-for-okta/main/).
