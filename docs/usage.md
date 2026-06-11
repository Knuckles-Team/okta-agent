# Usage

## Python API client

```python
from okta_agent import Api
from okta_agent.api.credentials import SswsToken

api = Api(org_url="https://acme.okta.com", credential=SswsToken("<token>"))

active = api.search_users(
    conditions=[{"field": "status", "op": "eq", "value": "ACTIVE"}],
    max_items=500,
)
print(active["count"], active["rate_limit"], active["next_cursor"])
```

Or build from the environment:

```python
from okta_agent.auth import get_client

api = get_client()
api.list_groups(q="eng")
```

## MCP server

```bash
okta-mcp                                  # stdio
okta-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

### Tool calls

List users by SCIM filter (built safely from conditions):

```json
{
  "action": "search",
  "params_json": "{\"conditions\": [{\"field\": \"profile.department\", \"op\": \"eq\", \"value\": \"Engineering\"}]}"
}
```

Create an OIDC app from the template:

```json
{
  "action": "create",
  "params_json": "{\"template\": \"oidc\", \"label\": \"Portal\", \"settings\": {\"redirect_uris\": [\"https://portal.example.com/cb\"]}}"
}
```

Query the system log (capped, resumable):

```json
{
  "action": "logs",
  "params_json": "{\"since\": \"2026-06-01T00:00:00Z\", \"filter\": \"eventType eq \\\"user.session.start\\\"\", \"limit\": 200}"
}
```

Destructive operations require explicit consent:

```json
{
  "action": "clear_sessions",
  "params_json": "{\"user_id\": \"00u1\", \"oauth_tokens\": true}",
  "allow_destructive": true
}
```

## Agent server

```bash
okta-agent --provider openai --model-id gpt-4o --port 9000
```
