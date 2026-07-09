# Okta MCP Agent Specs

> Claude Code loads this file via `CLAUDE.md` (`@AGENTS.md` import) — the two stay
> in sync. Edit **this** file, not `CLAUDE.md`.

This file acts as a machine-readable README for AI coding agents collaborating on this repository.

## Tech Stack & Architecture
- **Language**: Python >= 3.11
- **Ecosystem**: `agent-utilities` Dynamic Facade
- **MCP Server**: FastMCP (stdio and HTTP support)
- **HTTP**: raw `httpx` against the Okta Management API (no Okta SDK)
- **Key Files**:
  - `okta_agent/mcp_server.py`: FastMCP entry point and tool registration.
  - `okta_agent/api_client.py`: API facade composing the domain modules.
  - `okta_agent/auth.py`: Credentials loading (SSWS / private-key-JWT) and client builder.
  - `okta_agent/api/api_client_base.py`: rate limits, 429 backoff, pagination, error mapping, redaction.
  - `okta_agent/mcp/common.py`: destructive-action gate and error envelopes.

### Architecture Diagram
```mermaid
graph TD
    User([User/A2A]) --> Server[A2A Server / FastAPI]
    Server --> Agent[Pydantic AI Agent]
    Agent --> MCP[MCP Server / FastMCP]
    MCP --> Client[API Client / httpx]
    Client --> ExternalAPI([Okta Management API])
```

### Workflow Diagram
```mermaid
sequenceDiagram
    participant U as User
    participant S as Server
    participant A as Agent
    participant T as MCP Tool
    participant API as Okta API

    U->>S: Request
    S->>A: Process Query
    A->>T: Invoke Tool
    T->>API: API Request
    API-->>T: API Response
    T-->>A: Tool Result
    A-->>S: Final Response
    S-->>U: Output
```

## Commands

### Quality & Linting
Run pre-commit hooks locally:
```bash
pre-commit run --all-files
```

### Execution & Run
Launch the FastMCP server in stdio mode:
```bash
python -m okta_agent.mcp_server
```

### Testing Suite
Execute the entire test suite (mocked httpx — no live Okta calls):
```bash
pytest -v
```

## Project Structure

### File Tree
```text
.
├── .bumpversion.cfg
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── a2a.json
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
├── MANIFEST.in
├── mcp_config.json
├── mkdocs.yml
├── opencode.json
├── pyproject.toml
├── pytest.ini
├── README.md
├── requirements.txt
├── uv.lock
├── docker
│   ├── Dockerfile
│   ├── debug.Dockerfile
│   ├── agent.compose.yml
│   ├── mcp.compose.yml
│   └── starship.toml
├── docs
│   ├── concepts.md
│   ├── deployment.md
│   ├── index.md
│   ├── installation.md
│   ├── overview.md
│   └── usage.md
├── scripts
│   ├── security_sanitizer.py
│   ├── validate_a2a_agent.py
│   ├── validate_agent.py
│   └── verify_api_integration.py
├── tests
│   ├── conftest.py
│   ├── test_api_wrapper.py
│   ├── test_apps_client.py
│   ├── test_auth.py
│   ├── test_concept_parity.py
│   ├── test_credentials.py
│   ├── test_filters.py
│   ├── test_groups_client.py
│   ├── test_init_dynamics.py
│   ├── test_okta_mcp_validation.py
│   ├── test_okta_models.py
│   ├── test_pagination.py
│   ├── test_policies_client.py
│   ├── test_startup.py
│   ├── test_system_client.py
│   └── test_users_client.py
└── okta_agent
    ├── __init__.py
    ├── __main__.py
    ├── agent_server.py
    ├── api
    │   ├── __init__.py
    │   ├── api_client_apps.py
    │   ├── api_client_base.py
    │   ├── api_client_groups.py
    │   ├── api_client_policies.py
    │   ├── api_client_system.py
    │   ├── api_client_users.py
    │   ├── credentials.py
    │   └── filters.py
    ├── api_client.py
    ├── auth.py
    ├── main_agent.json
    ├── mcp
    │   ├── __init__.py
    │   ├── common.py
    │   ├── mcp_apps.py
    │   ├── mcp_groups.py
    │   ├── mcp_policies.py
    │   ├── mcp_system.py
    │   └── mcp_users.py
    ├── mcp_config.json
    ├── mcp_server.py
    ├── okta_input_models.py
    └── okta_response_models.py
```

## Concept Registry

| Concept ID | Name | Description |
|------------|------|-------------|
| `CONCEPT:OK-OS.governance.okta` | Core API Client Operations | Raw httpx Okta client: rate limits, backoff, pagination, error mapping |
| `CONCEPT:OK-OS.identity.okta` | Credential Strategies | SSWS token + OAuth2 private-key-JWT (Okta API scopes) |
| `CONCEPT:OK-OS.governance.okta-2` | FastMCP Tools Execution | Action-routed users/groups/apps/policies/system tools |
| `CONCEPT:OK-OS.identity.default` | Safety Gating & Redaction | `allow_destructive` gate (default false) + secret redaction |
| `CONCEPT:OK-OS.governance.okta-3` | SCIM Filter Building | Escaped, structured `filter` expression construction |
| `CONCEPT:AU-ECO.messaging.native-backend-abstraction` | Ecosystem Compliance | Multi-package integration compliance standard |

## Domain Rules

- **Keycloak parity**: where a concept exists in both IdPs, keep the verb
  identical to `keycloak-agent` (list/get/create/update, reset_password,
  members add/remove). Okta-specific verbs (suspend, group rules, zones) may
  diverge.
- **Destructive gate**: any new HTTP `DELETE`-class action, lifecycle
  degradation (deactivate/suspend), session clear, or password operation goes
  into the tool's `DESTRUCTIVE_*_ACTIONS` set and must be covered by a gating
  test.
- **Policy writes**: policy/rule create+update are intentionally out of scope
  in this release — do not add them without org-lockout safeguards.
- **Citations**: every API method docstring cites its
  `developer.okta.com` endpoint reference.
- **No live calls in tests**: all tests run against `httpx.MockTransport`.

---

## When Stuck
1. Check the mock transport fixtures in `tests/conftest.py`.
2. Propose an Implementation Plan first before adding new endpoints.

## ⛔ No Scratch or Temporary Files in Repository

**NEVER write any of the following to this repository:**
- Temporary test scripts (`test_*.py`, `debug_*.py` outside of `tests/`)
- Scratch scripts or experimental one-off files
- Log files (`.log`, `.txt` command output)
- Random text files with command output or debug dumps
- Any file that is NOT production source code, tests in `tests/`, or documentation

**Why:** These files expose private filesystem paths, credentials, and internal infrastructure details when pushed to GitHub publicly.

**Where to put scratch work instead:**
- Use `~/workspace/scratch/` for temporary scripts and experiments
- Use `~/workspace/reports/` for command output and reports
- Keep test scripts in the `tests/` directory following proper pytest conventions


## ⛔ Keep the Repository Root Pristine — No Scratch / Temp / Debug Files

**The repository ROOT must contain only canonical project files** (packaging,
config, docs, lockfiles). The only hidden directories allowed at root are
`.git/`, `.github/`, and `.specify/` (plus a local, git-ignored `.venv/`).

**NEVER write any of the following — anywhere in the repo, and ESPECIALLY at the root:**
- One-off / debug / migration scripts: `fix_*.py`, `migrate_*.py`, `refactor_*.py`,
  `replace_*.py`, `update_*.py`, `debug_*.py`, or `test_*.py` **at the root**
  (real tests live in `tests/` only).
- Databases / data dumps: `*.db`, `*.db-wal`, `*.sqlite*`, `*.corrupted`.
- Logs / command output: `*.log`, scratch `*.txt`, `*.orig`, `*.rej`, `*.bak`.
- Build artifacts: `*.tsbuildinfo`, compiled binaries, coverage files.
- AI agent scratch directories: `.agent/`, `.agents/`, `.agent_data/`, `.tmp/`,
  `.hypothesis/`, or any per-tool cache committed to git.
- Any file that is NOT production source, a test in `tests/`, documentation, or
  a recognized config/lockfile.

**Why:** scratch at the root leaks private paths/credentials, bloats the tree,
and erodes a pristine codebase.

**Where scratch goes instead:** `~/workspace/scratch/` (experiments),
`~/workspace/reports/` (command output); tests go in `tests/` (pytest).
Before finishing a task, run `git status` and confirm no stray root files were added.

## Working Discipline — think, simplify, stay surgical, verify

These four habits cut the most common LLM coding mistakes. For trivial tasks, use
judgment; the bias here is correctness over speed.

- **Think before coding.** State your assumptions explicitly. If a request has more than
  one reasonable reading, surface the options instead of silently picking one. If a
  simpler approach exists, say so and push back when warranted. When something is
  genuinely unclear, stop and name what's confusing — ask, don't guess.
- **Simplicity first.** Write the minimum code that solves the stated problem — no
  speculative features, no abstraction for single-use code, no configurability that
  wasn't requested, no error handling for impossible states. If you wrote 200 lines and
  it could be 50, rewrite it. (Name code from its purpose, never `wave0`/`phase2`/`v2`.)
- **Stay surgical.** Every changed line should trace directly to the task. Don't refactor,
  reformat, or "improve" working code adjacent to your change; match the existing style
  even where you'd do it differently. Remove only the imports/symbols your own change
  orphaned; if you spot unrelated dead code, mention it rather than deleting it inline.
  *Exception — the Quality Bar below:* lint/format/type errors the pre-commit gate flags
  get fixed regardless of who introduced them. In short: **surgical on behavior, clean on
  lint.**
- **Verify against a goal.** Turn the task into a checkable outcome before you start:
  "fix the bug" → "write a failing test that reproduces it, then make it pass"; "add
  validation" → "tests for the invalid inputs pass". For multi-step work, state the short
  plan and the check for each step, then loop until the checks pass.

## Quality Bar — Leave the Codebase Clean (REQUIRED)

After completing any code change, run the project's pre-commit suite and drive it
**fully green** before committing:

```bash
pre-commit run --all-files
```

Resolve **every** issue it reports — failures, lint errors, type errors, and
warnings — **including problems that pre-date your change and were not caused by
your edits**. The standing goal is a clean, working codebase with **no errors and
no warnings**. Do not silence checks (`# noqa`, `# type: ignore`, `SKIP=`,
`--no-verify`) to force green unless the exception is already documented in this
file as a known, unavoidable limitation. Only commit once `pre-commit run
--all-files` passes cleanly; if a check legitimately cannot pass, stop and explain
why rather than bypassing it.

## Working with Git Worktrees (multi-session)

Multiple agents/sessions work the `agent-packages/*` repos concurrently. **Do not
edit the canonical checkout** (`/home/apps/workspace/agent-packages/<repo>`) — a
background `repository-manager` sync can reset its working tree and discard
uncommitted edits. Take your own git worktree on your own branch instead:

```bash
# preferred — repository-manager MCP:
rm_worktree add <repo> <your-branch>      # -> /home/apps/worktrees/<repo>/<your-branch>

# raw-git fallback:
git -C agent-packages/<repo> checkout main
git -C agent-packages/<repo> worktree add /home/apps/worktrees/<repo>/<branch> -b <branch>
```

Work in the worktree and **commit often** (commits survive a working-tree reset).
Each session must use a **distinct branch** — git allows a branch in only one
worktree, which is what keeps concurrent sessions from colliding. Worktrees live
under `/home/apps/worktrees/` (outside the workspace scan, so the sync leaves them
alone).

**Finishing work in a worktree** — run this sequence before calling it done:
1. **Pre-commit green** — `pre-commit run --all-files`; resolve every issue per the
   Quality Bar above (including pre-existing), no `--no-verify`.
2. **Commit** in the worktree.
3. **Merge to main locally** — `rm_worktree merge <repo> <branch> --into main`
   (or `git merge --no-ff`). Push only when the user asks.
4. **Clean up** — remove the worktree and delete the merged branch:
   `rm_worktree remove <repo> <branch> --delete-branch`; `rm_worktree prune` clears
   stale entries. (Raw-git: `git worktree remove <path> && git branch -d <branch>`.)

<!-- BEGIN concept-coordination (generated) -->
## Concept-ID Coordination (multi-session)

Working in parallel with other sessions/worktrees? **Reserve a concept id before you write its `CONCEPT:` marker** so two sessions never collide:

```bash
agent-utilities --json concept reserve --ns EG-KG.compute.backend   # or a package prefix, e.g. KEY
```

Full protocol (ledger, merge=union, reconcile, MCP/REST): <https://knuckles-team.github.io/agent-utilities/concept_coordination/>
<!-- END concept-coordination (generated) -->

## Version & lockfile drift edict (keep the version mirrors AND the lock in sync)

The two most common release-breakers in this fleet are **version drift** (the version in
`pyproject.toml`/`.bumpversion.cfg` advancing while `README.md`, `docker/Dockerfile`, and the
module `__version__`s lag) and a **stale `uv.lock`** (shipping known-vulnerable transitive deps).
A version mismatch makes the next `bump-my-version` throw `VersionNotFoundException`; a stale lock
is what Dependabot flags. Rules:

1. **Never hand-edit a version string.** Change the version ONLY via
   `bump-my-version bump {patch|minor|major}` (a.k.a. `bump2version`), which rewrites every file
   registered in `.bumpversion.cfg` in one atomic, tagged commit. If you edited the version in
   `pyproject.toml` by hand, you created drift — revert and use the bumper.
2. **Every version-bearing file must be registered in `.bumpversion.cfg`** — at minimum
   `pyproject.toml` AND `README.md`, plus `docker/Dockerfile` and any module `__version__`. Never
   add a file that embeds the version without a `[bumpversion:file:...]` entry for it.
3. **Re-lock on every dependency change.** After editing `pyproject.toml` deps/extras, run
   `uv lock` and commit `uv.lock` in the SAME change. The `uv-lock` pre-commit hook runs with
   `--locked` and fails on drift — never bypass it. The committed `uv.lock` is the
   Dependabot/security surface.
4. **Patch CVEs with a version floor at the source, then re-lock.** `uv` resolves one version
   graph-wide, so a lower-bound in the extra that pulls a dependency raises it for the whole lock.
