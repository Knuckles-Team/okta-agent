---
name: okta-agent-development
skill_type: skill
domain: development
description: >-
  Develop, test, gate, and release the okta-agent connector. Use this skill when
  changing Okta API mappings, MCP tools, packaging, documentation, or repository
  gates.
license: MIT
tags: [okta, development, connector, test, gates]
tier: repository
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---

# okta-agent development

This repository owns the Okta Management API transport, mappings, MCP tools, and
packaged connector content. Shared connector contracts and transports belong to
`scion-sdk`; admission, serving, and durable graph state belong to
their owning repositories. Read `AGENTS.md` before changing code and keep
provider credentials, customer data, and private endpoints out of source,
logs, and skill content.

## Rapid delivery: the 5-minute contract

Specs are already designed. Deliver small, reviewable slices and cite the
owning spec row in the commit trailer.

- Find the owning row first with `git grep -n "<term>" -- specs` and extend the
  existing spec before adding new requirement text.
- Reuse the existing raw `httpx` client, auth policy, action-routed tool
  modules, and SDK facade. Do not create a second Okta transport or route.
- Bind every delivered requirement to a focused test. Generated `status.json`
  files are produced by `pipelines-hook spec-status`; never hand-edit them.
- Keep the connector boundary intact: Okta calls and mappings live here, while
  shared MCP contracts and admission live in their owning repositories.
- Put `Spec: <ID>` and the assisting agent trailer on consecutive final commit
  message lines.

## Setup and gates

Use the pinned environment and run the shared gate from the checkout root:

```bash
uv sync --locked
uvx pre-commit run --all-files
```

For focused feedback, use the mocked tests that exercise the actual connector
paths:

```bash
uv run --all-extras pytest tests/test_publication_workflow.py -q
uv run --all-extras pytest tests/test_startup.py tests/test_okta_mcp_validation.py -q
```

The external Okta API is never called by local tests. Use `httpx.MockTransport`
and keep credentials out of fixtures. Preserve SSWS and private-key-JWT auth,
credential redaction, rate-limit snapshots, cursor pagination, and the
`allow_destructive` safety gate when changing the client or tools.

## Packaging and publication

Keep `okta_agent/skills/`, `okta_agent/ontology/`, prompts, and connector data
in the package-data declaration. Build locally with `uv build` and inspect the
wheel contents before release. The canonical Pages publisher is
`.github/workflows/pages.yml`, which calls the shared pipelines workflow with
`.config/spec-dashboard.json`; keep its `workflow_dispatch` path and do not add
another documentation publisher. The generated dashboard reads
`specs/*/status.json` and is published at `spec-delivery/`.

Before pushing, work in a real Git worktree based on `origin/main`, inspect the
complete diff, stage only reviewed paths, and verify `git status --short` after
each gate. Do not use `git stash`, `git add -A`, `git add .`, or force-push.
Do not claim Pages publication until a successful exact-source workflow run and
the public dashboard are both observed.
