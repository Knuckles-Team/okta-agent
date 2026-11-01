# CONN-OKTA-AGENT-CONNECTOR-IDENTITY — The connector is filed under its fleet name

Owner: okta-agent. Cross-repo IDs: `SCION-CONNECTOR-CONTROL-R071`, `PIPE-GATES-R010`.

## Purpose and user stories

The engine and arbora list a connector's tools and ingest under its fleet name. This connector's fleet name is `okta-mcp`.

## Delivery mapping

Component: okta-agent connector

Code: ../../okta_agent/__init__.py

## Why a new spec

Searched `specs/` of `okta-agent` with `git grep` for the terms of this spec. No other spec of this repository owns the capability, so this spec owns it.

## User Scenarios & Testing

### User Story 1 - Fleet name (Priority: P1)

The fleet operator and the engine rely on this behaviour of `okta-agent`: `pyproject.toml` declares `okta-mcp` as the single `scion_sdk.connector` entry point. It is proven independently of the other stories.

**Acceptance Scenarios**:

1. **Given** the `okta-agent` connector built from the default branch, **When** `tests/test_fleet_name.py::test_connector_name_is_the_fleet_name` runs, **Then** every connector name in the package is `okta-mcp`.

### Edge Cases

- The vendor service is unreachable or rejects the credential: the connector returns the SDK typed error and never a partial result.
- An argument outside the documented inputs is refused with the SDK typed refusal and causes no effect on the vendor service.

## Requirements

- **FR-001**: Fleet name. Rows: `CONN-OKTA-AGENT-CONNECTOR-IDENTITY-R001`.

## Success Criteria

- **SC-001**: Every connector name in the package is `okta-mcp`. Rows: `CONN-OKTA-AGENT-CONNECTOR-IDENTITY-R001`.

## Assumptions

- The `okta-agent` package keeps the entry point and module layout named in the rows.
- The shared SDK supplies the transport, authentication, retry and certification helpers the rows reuse.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-OKTA-AGENT-CONNECTOR-IDENTITY-R001` | plan.md Production caller chain | T-001 | tests/test_fleet_name.py::test_connector_name_is_the_fleet_name |
