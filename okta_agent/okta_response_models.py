"""CONCEPT:OKTA-1.1 Typed response-envelope models for the Okta tool surface.

Pydantic models mirroring the response envelopes produced by
:class:`okta_agent.api.api_client_base.ApiClientBase` and the destructive-gate
and error mapping in :mod:`okta_agent.mcp.common`. Programmatic callers can
parse tool results into these models with ``Model.model_validate(result)``.
"""

from typing import Any

from pydantic import BaseModel, Field


class RateLimitSnapshot(BaseModel):
    """Latest ``X-Rate-Limit-*`` header snapshot captured from the org."""

    limit: int | None = Field(default=None, description="X-Rate-Limit-Limit.")
    remaining: int | None = Field(default=None, description="X-Rate-Limit-Remaining.")
    reset: int | None = Field(
        default=None, description="X-Rate-Limit-Reset (epoch seconds)."
    )


class ResponseEnvelope(BaseModel):
    """Successful tool/API response: ``data`` plus the rate-limit snapshot.

    List endpoints additionally report ``count``, ``truncated`` and — when
    more data remains — the ``next_cursor`` to resume from.
    """

    data: Any = Field(description="Response payload (object or list).")
    rate_limit: RateLimitSnapshot | None = Field(
        default=None, description="Latest rate-limit snapshot."
    )
    count: int | None = Field(default=None, description="Items in this page set.")
    truncated: bool | None = Field(
        default=None, description="True when the item cap stopped pagination."
    )
    next_cursor: str | None = Field(
        default=None, description="Okta `after` cursor to resume from."
    )


class ErrorDetail(BaseModel):
    """Okta error envelope mapped from ``errorCode``/``errorSummary``/etc."""

    status: int | None = Field(default=None, description="HTTP status code.")
    error_code: str | None = Field(default=None, description="Okta errorCode.")
    error_summary: str | None = Field(
        default=None, description="Okta errorSummary (credential-redacted)."
    )
    error_id: str | None = Field(default=None, description="Okta errorId.")
    error_causes: list[dict[str, Any]] = Field(
        default_factory=list, description="Okta errorCauses entries."
    )
    rate_limit: RateLimitSnapshot | None = Field(
        default=None, description="Rate-limit snapshot at failure time."
    )
    message: str | None = Field(
        default=None,
        description="Local error message (bad params / destructive gate).",
    )
    destructive_actions: list[str] | None = Field(
        default=None,
        description="The tool's gated actions, reported by the destructive gate.",
    )


class ErrorEnvelope(BaseModel):
    """Failed tool response: ``{"error": {...}}``."""

    error: ErrorDetail = Field(description="Structured error detail.")
