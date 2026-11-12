# CONN-OKTA-AGENT-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-OKTA-AGENT-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py::test_default_content_surfaces` (planned) | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
| T-002 | `CONN-OKTA-AGENT-CONNECTOR-CONTENT-R002` | `tests/test_destructive_gate.py::test_declared_operations_are_destructive_tools_that_ask_first` | Each of the 13 served tools has `destructiveHint` true and a `confirm` argument and none has `allow_destructive`; a call without `confirm` sends no request, and `confirm=true` sends one. |

## Negative and boundary cases

Each proving test above includes the refusal or error case that its row names. A vendor outage or an unauthorised call must return the SDK typed error.

## Quality and release proof

Run `uv run pytest tests` and `pre-commit run --all-files` from the repository root. A planned test is added by the code change that lands the row.
