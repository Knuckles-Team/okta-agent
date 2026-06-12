# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`okta-agent` exposes its MCP server (console script `okta-mcp`) four ways. Pick the row that
matches where the server runs relative to your MCP client, then copy the matching
`mcp_config.json` below. Replace the `<your-…>` placeholders with the values from the **Configuration / Environment Variables** section.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container / uv | `stdio` or `streamable-http` | Docker / Podman / uv on this host | `command` or `url` |
| 4 | Remote URL | `streamable-http` | a remote host behind Caddy | `url` |

### 1. stdio (local subprocess)

The client launches the server over stdio via `uvx` — best for local IDEs
(Cursor, Claude Desktop, VS Code):

```json
{
  "mcpServers": {
    "okta-mcp": {
      "command": "uvx",
      "args": ["--from", "okta-agent", "okta-mcp"],
      "env": {
        "OKTA_ORG_URL": "<your-okta_org_url>",
        "OKTA_API_TOKEN": "<your-okta_api_token>",
        "OKTA_PRIVATE_KEY": "<your-okta_private_key>"
      }
    }
  }
}
```

### 2. Streamable-HTTP (local process)

Run the server as a long-lived HTTP process:

```bash
uvx --from okta-agent okta-mcp --transport streamable-http --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health        # {"status":"OK"}
```

Then either let the client launch it:

```json
{
  "mcpServers": {
    "okta-mcp": {
      "command": "uvx",
      "args": ["--from", "okta-agent", "okta-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "OKTA_ORG_URL": "<your-okta_org_url>",
        "OKTA_API_TOKEN": "<your-okta_api_token>",
        "OKTA_PRIVATE_KEY": "<your-okta_private_key>"
      }
    }
  }
}
```

…or connect to the already-running process by URL:

```json
{
  "mcpServers": {
    "okta-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 3. Local container / uv

**(a) Launch a container directly from `mcp_config.json`** (stdio over the container —
no ports to manage). Swap `docker` for `podman` for a daemonless runtime:

```json
{
  "mcpServers": {
    "okta-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRANSPORT=stdio",
        "-e", "OKTA_ORG_URL=<your-okta_org_url>",
        "-e", "OKTA_API_TOKEN=<your-okta_api_token>",
        "-e", "OKTA_PRIVATE_KEY=<your-okta_private_key>",
        "knucklessg1/okta-agent:latest"
      ]
    }
  }
}
```

**(b) Run a local streamable-http container, then connect by URL:**

```bash
docker run -d --name okta-mcp -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  -e OKTA_ORG_URL="<your-okta_org_url>" \
  -e OKTA_API_TOKEN="<your-okta_api_token>" \
  -e OKTA_PRIVATE_KEY="<your-okta_private_key>" \
  knucklessg1/okta-agent:latest
# or, from a clone of this repo:
docker compose -f docker/mcp.compose.yml up -d
```

```json
{
  "mcpServers": {
    "okta-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

**(c) From a local checkout with `uv`:**

```bash
uv run okta-mcp --transport streamable-http --port 8000
```

### 4. Remote URL (deployed behind Caddy)

When the server is deployed remotely (e.g. as a Docker service) and published through
Caddy on the internal `*.arpa` zone, connect with the `"url"` key — no local process or
image required:

```json
{
  "mcpServers": {
    "okta-mcp": { "url": "http://okta-mcp.arpa/mcp" }
  }
}
```

Caddy reverse-proxies `http://okta-mcp.arpa` to the container's `:8000`
streamable-http listener; `http://okta-mcp.arpa/health` returns
`{"status":"OK"}` when the service is live.
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
docker build -f docker/Dockerfile -t knucklessg1/okta-agent:latest .
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
| `OKTA_SSL_VERIFY` | Verify TLS certificates (`True`/`False`) |
| `OKTA_ALLOW_DESTRUCTIVE` | Org-wide default for destructive tool actions |
| `HOST` / `PORT` / `TRANSPORT` | MCP server bind + transport |
| `USERSTOOL` … `SYSTEMTOOL` | Per-domain tool toggles |

Mount secrets (API token, private key) from your secret store; never bake them
into the image. Keep `OKTA_ALLOW_DESTRUCTIVE=False` in shared deployments.

## Reverse proxy + DNS (Caddy + Technitium)

For fleet deployments, publish the MCP server behind Caddy and register the
hostname in Technitium DNS:

```caddyfile
okta-mcp.arpa {
    reverse_proxy okta-agent-mcp:8000
}
```

Point an `A` record for `okta-mcp.arpa` at the ingress node in Technitium, then
use `https://okta-mcp.arpa/mcp` as the client `MCP_URL` and
`https://okta-mcp.arpa/health` as the health-check target.
