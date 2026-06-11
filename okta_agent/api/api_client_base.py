"""CONCEPT:OKTA-1.1 Shared httpx base client for the Okta Management API.

Responsibilities:

- per-request auth-header injection from a credential strategy
  (:mod:`okta_agent.api.credentials`);
- rate-limit awareness — captures ``X-Rate-Limit-Limit`` /
  ``X-Rate-Limit-Remaining`` / ``X-Rate-Limit-Reset`` on every response and
  exposes them in every response envelope
  (https://developer.okta.com/docs/reference/rl-best-practices/);
- automatic capped backoff + retry on HTTP 429, sleeping until the
  ``X-Rate-Limit-Reset`` epoch (never longer than ``backoff_cap`` seconds);
- cursor pagination via RFC 5988 ``Link: <...>; rel="next"`` headers — Okta's
  ``after`` cursor pattern (https://developer.okta.com/docs/api/#pagination);
- Okta error-envelope mapping (``errorCode`` / ``errorSummary`` / ``errorId``
  / ``errorCauses`` → :class:`OktaApiError`)
  (https://developer.okta.com/docs/reference/error-codes/);
- CONCEPT:OKTA-1.4 secret redaction — credential material never appears in
  logs or raised error messages.
"""

import re
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from agent_utilities.base_utilities import get_logger

from okta_agent.api.credentials import NoCredential, OktaCredential

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_CAP = 60.0
#: Default overall item cap for paginated list calls.
DEFAULT_MAX_ITEMS = 1000

REDACTED = "***REDACTED***"
_AUTH_SCHEME_RE = re.compile(r"\b(SSWS|Bearer)\s+[A-Za-z0-9._~+/=-]+")


def redact_secrets(text: str, secrets: list[str] | None = None) -> str:
    """Strip credential material from arbitrary text (CONCEPT:OKTA-1.4).

    Replaces every known secret value and any ``SSWS <token>`` /
    ``Bearer <token>`` pattern with ``***REDACTED***``.
    """
    for secret in secrets or []:
        if secret:
            text = text.replace(secret, REDACTED)
    return _AUTH_SCHEME_RE.sub(rf"\1 {REDACTED}", text)


class OktaApiError(Exception):
    """An Okta Management API error, mapped from Okta's error envelope.

    Okta errors carry ``errorCode``, ``errorSummary``, ``errorId`` and
    ``errorCauses`` (https://developer.okta.com/docs/reference/error-codes/).
    The summary is pre-redacted of credential material.
    """

    def __init__(
        self,
        status: int,
        error_code: str | None = None,
        error_summary: str | None = None,
        error_id: str | None = None,
        error_causes: list[dict[str, Any]] | None = None,
        rate_limit: dict[str, int] | None = None,
    ):
        self.status = status
        self.error_code = error_code
        self.error_summary = error_summary
        self.error_id = error_id
        self.error_causes = error_causes or []
        self.rate_limit = rate_limit
        super().__init__(f"Okta API error {status} ({error_code}): {error_summary}")

    def to_dict(self) -> dict[str, Any]:
        """Serializable error envelope for MCP tool responses."""
        return {
            "status": self.status,
            "error_code": self.error_code,
            "error_summary": self.error_summary,
            "error_id": self.error_id,
            "error_causes": self.error_causes,
            "rate_limit": self.rate_limit,
        }


class ApiClientBase:
    """Raw httpx client for one Okta org (no Okta SDK)."""

    def __init__(
        self,
        org_url: str,
        credential: OktaCredential | None = None,
        verify: bool = True,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_cap: float = DEFAULT_BACKOFF_CAP,
        transport: httpx.BaseTransport | None = None,
    ):
        self.org_url = org_url.rstrip("/")
        self.credential = credential or NoCredential()
        self.max_retries = max_retries
        self.backoff_cap = backoff_cap
        #: Rate-limit snapshot from the most recent response.
        self.last_rate_limit: dict[str, int] | None = None
        self._client = httpx.Client(
            base_url=self.org_url,
            verify=verify,
            timeout=timeout,
            transport=transport,
        )

    # ------------------------------------------------------------------ #
    # Rate limiting
    # ------------------------------------------------------------------ #

    def _capture_rate_limit(self, response: httpx.Response) -> None:
        """Record X-Rate-Limit-* headers from a response."""
        snapshot: dict[str, int] = {}
        for key, header in (
            ("limit", "X-Rate-Limit-Limit"),
            ("remaining", "X-Rate-Limit-Remaining"),
            ("reset", "X-Rate-Limit-Reset"),
        ):
            value = response.headers.get(header)
            if value is not None:
                try:
                    snapshot[key] = int(value)
                except ValueError:
                    continue
        if snapshot:
            self.last_rate_limit = snapshot

    def _backoff_seconds(self, response: httpx.Response) -> float:
        """Seconds to wait after a 429, derived from X-Rate-Limit-Reset.

        Okta's reset header is an epoch timestamp; the wait is clamped to
        ``[1.0, backoff_cap]`` so a skewed clock can never stall the client.
        """
        wait = 1.0
        reset = response.headers.get("X-Rate-Limit-Reset")
        if reset is not None:
            try:
                wait = float(reset) - time.time()
            except ValueError:
                wait = 1.0
        return max(1.0, min(wait, self.backoff_cap))

    # ------------------------------------------------------------------ #
    # Core request plumbing
    # ------------------------------------------------------------------ #

    def _request_raw(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> httpx.Response:
        """Perform one request with auth injection and 429 backoff.

        ``url`` may be a path (resolved against the org URL) or an absolute
        URL (as returned in pagination ``Link`` headers).
        """
        attempt = 0
        while True:
            headers = {"Accept": "application/json"}
            if json_body is not None:
                headers["Content-Type"] = "application/json"
            headers.update(self.credential.headers())

            logger.debug("Okta request: %s %s", method, redact_secrets(url))
            response = self._client.request(
                method, url, params=params, json=json_body, headers=headers
            )
            self._capture_rate_limit(response)

            if response.status_code == 429 and attempt < self.max_retries:
                wait = self._backoff_seconds(response)
                attempt += 1
                logger.warning(
                    "Okta rate limit hit (429); backing off %.1fs "
                    "(attempt %d/%d, remaining=%s)",
                    wait,
                    attempt,
                    self.max_retries,
                    (self.last_rate_limit or {}).get("remaining"),
                )
                time.sleep(wait)
                continue

            if response.status_code >= 400:
                raise self._map_error(response)
            return response

    def _map_error(self, response: httpx.Response) -> OktaApiError:
        """Map an Okta error response to :class:`OktaApiError` (redacted)."""
        try:
            body = response.json()
            if not isinstance(body, dict):
                body = {}
        except Exception:
            body = {}
        secrets = self.credential.secrets()
        summary = redact_secrets(
            str(body.get("errorSummary") or response.text[:500]), secrets
        )
        return OktaApiError(
            status=response.status_code,
            error_code=body.get("errorCode"),
            error_summary=summary,
            error_id=body.get("errorId"),
            error_causes=body.get("errorCauses"),
            rate_limit=self.last_rate_limit,
        )

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        """Perform a request and return the parsed JSON body.

        Returns ``{"status": "success"}`` for empty/204 responses. Raises
        :class:`OktaApiError` on HTTP >= 400 (after capped 429 retries).
        """
        response = self._request_raw(method, path, params=params, json_body=json_body)
        if response.status_code == 204 or not response.text.strip():
            return {"status": "success"}
        return response.json()

    # ------------------------------------------------------------------ #
    # Response envelopes and pagination
    # ------------------------------------------------------------------ #

    def envelope(self, data: Any, **extra: Any) -> dict[str, Any]:
        """Wrap a result with the latest rate-limit snapshot."""
        return {"data": data, "rate_limit": self.last_rate_limit, **extra}

    def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        max_items: int = DEFAULT_MAX_ITEMS,
    ) -> dict[str, Any]:
        """GET a collection, following ``Link: rel="next"`` cursor pages.

        Follows Okta's ``after`` cursor (https://developer.okta.com/docs/api/#pagination)
        until the collection is exhausted or ``max_items`` is reached. The
        envelope reports ``count``, ``truncated`` and — when more data
        remains — the ``next_cursor`` to resume from.
        """
        items: list[Any] = []
        url = path
        page_params = dict(params or {})
        next_cursor: str | None = None
        truncated = False

        while True:
            response = self._request_raw("GET", url, params=page_params or None)
            page = response.json()
            if not isinstance(page, list):
                page = [page]
            items.extend(page)

            next_url = response.links.get("next", {}).get("url")
            next_cursor = _after_cursor(next_url) if next_url else None

            if len(items) >= max_items:
                truncated = len(items) > max_items or next_url is not None
                items = items[:max_items]
                break
            if not next_url:
                break
            url = next_url
            page_params = {}  # the next URL already carries the query string

        return self.envelope(
            items, count=len(items), truncated=truncated, next_cursor=next_cursor
        )


def _after_cursor(url: str | None) -> str | None:
    """Extract Okta's ``after`` cursor from a pagination URL."""
    if not url:
        return None
    values = parse_qs(urlparse(url).query).get("after")
    return values[0] if values else None


def drop_none(params: dict[str, Any]) -> dict[str, Any]:
    """Remove ``None`` values from a query-parameter dict."""
    return {k: v for k, v in params.items() if v is not None}
