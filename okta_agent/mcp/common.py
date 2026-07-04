"""CONCEPT:OK-OS.governance.okta-2 Shared helpers for the action-routed Okta MCP tools.

Each tool is a thin shim: it parses ``params_json``, enforces the
CONCEPT:OK-OS.identity.default destructive-action gate, dispatches to the corresponding
``Api`` method, and maps :class:`okta_agent.api.api_client_base.OktaApiError`
into a serializable error envelope. All API surface lives in
``okta_agent.api`` — these tools add no business logic.
"""

import json
from collections.abc import Callable
from typing import Any

from okta_agent.api.api_client_base import OktaApiError
from okta_agent.auth import allow_destructive_default


def parse_params(params_json: str) -> dict[str, Any]:
    """Parse a tool's ``params_json`` argument; raises ``ValueError`` if invalid."""
    if not params_json:
        return {}
    parsed = json.loads(params_json)
    if not isinstance(parsed, dict):
        raise ValueError("params_json must decode to a JSON object.")
    return parsed


def destructive_blocked(
    action: str, destructive_actions: set[str], allow_destructive: bool
) -> dict[str, Any] | None:
    """CONCEPT:OK-OS.identity.default Gate destructive actions behind explicit consent.

    Returns an error envelope when ``action`` is destructive and neither the
    per-call ``allow_destructive`` flag nor the ``OKTA_ALLOW_DESTRUCTIVE``
    environment default permits it; returns ``None`` when the call may proceed.
    """
    if action not in destructive_actions:
        return None
    if allow_destructive or allow_destructive_default():
        return None
    return {
        "error": {
            "message": (
                f"Action {action!r} is destructive and blocked by default. "
                "Re-run with allow_destructive=true (or set "
                "OKTA_ALLOW_DESTRUCTIVE=True) to confirm."
            ),
            "destructive_actions": sorted(destructive_actions),
        }
    }


def dispatch(call: Callable[[], Any]) -> Any:
    """Run an Api call, mapping Okta errors and bad params to error envelopes.

    ``call`` is a zero-argument closure so parameter extraction
    (``params["user_id"]`` etc.) happens *inside* the guard — a missing key
    becomes a structured error envelope, never an unhandled exception.
    """
    try:
        return call()
    except OktaApiError as exc:
        return {"error": exc.to_dict()}
    except KeyError as exc:
        return {"error": {"message": f"Missing required parameter: {exc}."}}
    except ValueError as exc:
        return {"error": {"message": str(exc)}}
