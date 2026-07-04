"""CONCEPT:OK-OS.governance.okta-3 SCIM-style filter expression builder for Okta list endpoints.

Okta list endpoints accept a SCIM 2.0-flavoured ``filter`` parameter, e.g.
``status eq "ACTIVE" and lastUpdated gt "2026-01-01T00:00:00.000Z"``.
This module builds those expressions safely (quoting and escaping values)
from structured conditions so callers never hand-concatenate filter strings.

Filter reference: https://developer.okta.com/docs/api/#filter
"""

from typing import Any

#: Operators supported by Okta's SCIM filter subset.
SCIM_OPERATORS = {"eq", "ge", "gt", "le", "lt", "ne", "sw", "co", "ew", "pr"}
JOINERS = {"and", "or"}


def scim_value(value: Any) -> str:
    """Render a Python value as a SCIM filter literal.

    Strings are double-quoted with embedded quotes/backslashes escaped;
    booleans become ``true``/``false``; numbers stay bare.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def scim_clause(field: str, op: str, value: Any = None) -> str:
    """Build one filter clause, e.g. ``status eq "ACTIVE"``.

    The ``pr`` (present) operator takes no value. Raises ``ValueError`` on
    unsupported operators or a missing value for binary operators.
    """
    op = op.lower()
    if op not in SCIM_OPERATORS:
        raise ValueError(
            f"Unsupported SCIM operator {op!r}; expected one of "
            f"{sorted(SCIM_OPERATORS)}."
        )
    if op == "pr":
        return f"{field} pr"
    if value is None:
        raise ValueError(f"SCIM operator {op!r} requires a value.")
    return f"{field} {op} {scim_value(value)}"


def build_filter(conditions: list[dict[str, Any]], joiner: str = "and") -> str:
    """Combine structured conditions into one SCIM filter expression.

    Each condition is ``{"field": ..., "op": ..., "value": ...}``; clauses are
    joined with ``and``/``or``. Example::

        build_filter([
            {"field": "status", "op": "eq", "value": "ACTIVE"},
            {"field": "profile.department", "op": "eq", "value": "Engineering"},
        ])
        # -> 'status eq "ACTIVE" and profile.department eq "Engineering"'
    """
    joiner = joiner.lower()
    if joiner not in JOINERS:
        raise ValueError(f"Joiner must be one of {sorted(JOINERS)}, got {joiner!r}.")
    if not conditions:
        raise ValueError("At least one filter condition is required.")
    clauses = [
        scim_clause(c["field"], c.get("op", "eq"), c.get("value")) for c in conditions
    ]
    return f" {joiner} ".join(clauses)
