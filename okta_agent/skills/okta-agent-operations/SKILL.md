---
name: okta-agent-operations
skill_type: skill
description: >-
  Operate okta-agent through its governed MCP and Arbora capabilities, including okta access management, okta directory ingestion, okta user lifecycle. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Okta Agent Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Steps

1. Confirm access by calling `okta_get_org`. Verify it returns the organization without an authentication error.
2. Pick the matching tool from the Tools list below, for example `okta_list_policies` for policies. Verify the tool name appears in that list.
3. Run read-only inspection first, for example `okta_get_policy` (`policy_id`). Verify the object you will change exists.
4. For a change, present the impact and call one tool, for example `okta_activate_policy`. Verify the response reports the new status.
5. For audit evidence, call `okta_get_system_log`. Verify an event for your action appears.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| 401 or 403 from Okta | `OKTA_ORG_URL` or `OKTA_API_TOKEN` missing or lacking rights | Set both variables with a token that has the needed admin role, then call `okta_get_org`. |
| Deactivate refused | `okta_deactivate_policy` or `okta_deactivate_policy_rule` ran without confirmation | Obtain explicit approval naming the policy, then call the tool again with `confirm=true`. |
| Empty policy list | Wrong policy `type` filter | Call `okta_list_policies` again with a valid type from the Okta policy types. |

## Tools

- Policies (read and lifecycle): `okta_list_policies`, `okta_get_policy`, `okta_list_policy_rules`, `okta_activate_policy`, `okta_activate_policy_rule`; destructive `okta_deactivate_policy`, `okta_deactivate_policy_rule`.
- Org and audit: `okta_get_org`, `okta_list_authorization_servers`, `okta_get_system_log`, `okta_list_authenticators`, `okta_list_org_factors`, `okta_list_network_zones`.
- Users, groups and applications: see `okta-user-lifecycle` and `okta-access-management`.
- Graph: `okta_ingest_users`, `okta_ingest_groups`, `okta_ingest_apps`, `okta_ingest_all`.

Destructive tools ask the caller to confirm (or take `confirm=true`); read and reversible work needs neither.

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.
