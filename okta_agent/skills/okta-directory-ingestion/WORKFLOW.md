# Okta Directory Ingestion

Natively mirror the Okta directory (users, groups, applications) into the medulla knowledge graph as typed OWL nodes via the okta-agent MCP server. Use when the agent must ingest or refresh Okta identities/groups/apps in the KG so they can be queried, related, and reasoned over alongside the rest of the ecosystem. Do NOT use for live user lifecycle (okta-user-lifecycle) or access administration (okta-access-management) — this is a read-and-push ingestion path only.

# Okta Directory Ingestion

The native "maximum ingestion" path for the Okta connector: list the directory
via the Okta Management API and push it into the ONE medulla knowledge
graph as typed nodes — `:User`, `:Group`, `:Application` — carrying provenance
(`source=okta-agent`, `domain=okta`). Best-effort and engine-guarded: it no-ops
cleanly when no graph engine is reachable.

## When to use
- Seed or refresh the KG with the current Okta users/groups/apps.
- Make Okta identities queryable/relatable next to other ecosystem data.
- Run a one-shot mirror before a graph query or an access-review workflow.

## When NOT to use
- Mutating users, membership, or app assignments → `okta-user-lifecycle` /
  `okta-access-management` (this path only reads Okta and writes the KG).
- Ad-hoc single-object reads → the typed `okta_list_users` / `okta_list_groups` /
  `okta_list_apps` tools directly.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`okta-agent`** MCP server. Needs
the same `OKTA_ORG_URL` + `OKTA_API_TOKEN` (or OAuth) credentials as the other
Okta skills, plus a reachable medulla engine for the write to land
(otherwise `ingested` comes back `null`).

## Tools
| Tool | Effect |
|------|--------|
| `okta_ingest_users` | List users and write `:User` nodes |
| `okta_ingest_groups` | List groups and write `:Group` nodes |
| `okta_ingest_apps` | List applications and write `:Application` nodes |
| `okta_ingest_all` | Ingest all three |

Each tool accepts `limit` (page size, default 200) and `max_items` (overall cap, default 1000)
to bound the listing pulled before ingestion. Node ids follow `okta:<class>:<oktaId>`; each `type`
matches a class federated by the `okta_agent.ontology` `okta.ttl`.

Declaratively, the same mapping is available to `source_sync` via the in-repo
`connectors/mcp_source_presets.json` presets (`okta-users` / `okta-groups` /
`okta-apps`).

## Recipes
Mirror the whole directory: call `okta_ingest_all` with no arguments.

Ingest just the first 500 users: `okta_ingest_users` with `limit` = 200 and `max_items` = 500.

## Gotchas
- The write is **best-effort**: with no reachable engine, `ingested` is `null`
  while `listed` still reports what was fetched — that is success, not an error.
- Ingestion is a snapshot mirror, not a subscription — re-run to pick up changes;
  nodes are MERGEd by id so re-runs are idempotent.
- Large orgs: cap with `max_items` and page via `limit` (200 max per Okta page)
  to avoid pulling the entire directory in one call.
- User `:memberOfGroup` edges are only written when the listing embeds group ids;
  a plain `list` does not, so run per-user `list_groups` or the group side for
  full membership edges.

## Related
- `okta-user-lifecycle`, `okta-access-management` — the operational tools whose
  objects this skill mirrors.
- The `okta_agent.kg_ingest` module (`ingest_users` / `ingest_groups` /
  `ingest_apps`) is the underlying mapper over the shared native-ingest primitive.
