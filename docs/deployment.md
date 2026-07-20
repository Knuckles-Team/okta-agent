# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`okta-agent` supports local stdio, a loopback-only development listener, a
least-privilege stdio container, and a remote authenticated HTTPS boundary.
Provider endpoint, credential, selector, identity, and trust material are supplied
at runtime through `AgentConfig`; none is stored in this repository.

### Installed stdio process

```json
{
  "mcpServers": {
    "okta": {
      "command": "okta-mcp",
      "args": [],
      "env": {"MCP_TOOL_MODE": "intent"}
    }
  }
}
```

### Loopback development listener

```bash
okta-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Do not expose this listener beyond loopback. Network deployments require direct TLS
or an explicitly trusted TLS-terminating ingress, configured authentication, exact
`MCP_ALLOWED_HOSTS`, and an exact trusted-proxy CIDR policy.

### Least-privilege local container

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  registry.example.invalid/okta-agent@sha256:<digest> okta-mcp
```

The operator projects the selected AgentConfig profile into the process at runtime;
the image remains immutable and contains no environment connection profile.

### Remote authenticated HTTPS endpoint

```json
{
  "mcpServers": {
    "okta": {"url": "https://service.example.invalid/mcp"}
  }
}
```

Store the real remote URL, outbound identity reference, and TLS-profile reference in
`AgentConfig`, not in MCP client JSON or documentation.
<!-- END GENERATED: deployment-options -->

## MCP server transports

=== "stdio (default)"

    ```bash
    okta-mcp
    ```

    For local agent integration — the MCP client owns the process and speaks
    JSON-RPC over stdin/stdout.

=== "streamable-http"

    ```bash
    okta-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```

    For networked deployments behind a reverse proxy. The server exposes
    `/mcp` for clients and `/health` for orchestrator checks.

=== "sse"

    ```bash
    okta-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

    Server-sent-events transport for clients that require it.

### Health check

```bash
curl -fsS http://localhost:8000/health
# {"status": "OK"}
```

## Docker Compose (MCP only)

```bash
cp .env.example .env   # fill in OKTA_ORG_URL + one auth mode
docker compose -f docker/mcp.compose.yml up -d
```

The MCP server listens on port `8000` (streamable-http) with a `/health` check.

## Docker Compose (MCP + Agent)

```bash
docker compose -f docker/agent.compose.yml up -d
```

This brings up both the `okta-agent-mcp` service (port 8000) and the
`okta-agent-agent` A2A service (port 9021, AG-UI web interface).

## Building the image

```bash
docker build -f docker/Dockerfile -t example/okta-agent:agent-local .
```

A `docker/debug.Dockerfile` is provided for an in-place editable install with
shell tooling and the Starship prompt.

## A2A agent server

```bash
okta-agent                        # standalone A2A server
```

The agent connects to the MCP server via `MCP_URL`
(`http://okta-agent-mcp:8000/mcp` in Compose) and exposes the A2A endpoint and
AG-UI web interface on its port.

## Environment

| Variable | Description |
|----------|-------------|
| `OKTA_ORG_URL` | Okta org URL (no trailing slash) |
| `OKTA_API_TOKEN` | SSWS API token (auth mode 1, takes precedence) |
| `OKTA_CLIENT_ID` / `OKTA_PRIVATE_KEY[_FILE]` / `OKTA_SCOPES` | OAuth2 private-key-JWT (auth mode 2) |
| `OKTA_TLS_PROFILE` | Named outbound TLS policy from AgentConfig |
| `OKTA_ALLOW_DESTRUCTIVE` | Org-wide default for destructive tool actions |
| `HOST` / `PORT` / `TRANSPORT` | MCP server bind + transport |
| `USERSTOOL` … `SYSTEMTOOL` | Per-domain tool toggles |

Mount secrets (API token, private key) from your secret store; never bake them
into the image. Keep `OKTA_ALLOW_DESTRUCTIVE=False` in shared deployments.

## Reverse proxy + DNS (Caddy + Technitium)

For fleet deployments, publish the MCP server behind Caddy and register the
hostname in Technitium DNS:

```caddyfile
okta-mcp.example.invalid {
    reverse_proxy okta-agent-mcp:8000
}
```

Point an `A` record for `okta-mcp.example.invalid` at the ingress node in Technitium, then
use `https://okta-mcp.example.invalid/mcp` as the client `MCP_URL` and
`https://okta-mcp.example.invalid/health` as the health-check target.
