"""Shared fixtures: mocked-httpx Okta API clients (no live Okta calls)."""

import json
from typing import Any

import httpx
import pytest

from okta_agent.api.credentials import SswsToken
from okta_agent.api_client import Api

ORG_URL = "https://test.okta.example.com"
#: Deliberately short fake token (sanitizer-safe), used across the suite.
TEST_TOKEN = "00fake-tok"

RATE_LIMIT_HEADERS = {
    "X-Rate-Limit-Limit": "600",
    "X-Rate-Limit-Remaining": "599",
    "X-Rate-Limit-Reset": "1700000000",
}


def json_response(
    data: Any,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Build a JSON response carrying Okta rate-limit headers."""
    all_headers = dict(RATE_LIMIT_HEADERS)
    if headers:
        all_headers.update(headers)
    return httpx.Response(
        status,
        content=json.dumps(data),
        headers={**all_headers, "Content-Type": "application/json"},
    )


def link_next(
    after: str, path: str = "/api/v1/users", limit: int = 2
) -> dict[str, str]:
    """Build an Okta-style pagination Link header for the next page."""
    return {
        "Link": f'<{ORG_URL}{path}?after={after}&limit={limit}>; rel="next"',
    }


class RequestRecorder:
    """Capture every request a mocked client makes."""

    def __init__(self, responder):
        self.requests: list[httpx.Request] = []
        self._responder = responder

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responder(request)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


@pytest.fixture
def make_api():
    """Factory producing an Api wired to a mock transport."""

    def _make(handler, **kwargs) -> Api:
        return Api(
            org_url=ORG_URL,
            credential=kwargs.pop("credential", SswsToken(TEST_TOKEN)),
            transport=httpx.MockTransport(handler),
            **kwargs,
        )

    return _make


@pytest.fixture
def recorded_api(make_api):
    """An Api whose handler echoes ``{}`` and records all requests."""
    recorder = RequestRecorder(lambda request: json_response({}))
    return make_api(recorder), recorder


@pytest.fixture(autouse=True)
def clean_okta_env(monkeypatch):
    """Keep ambient OKTA_* environment out of every test."""
    import os

    for key in list(os.environ):
        if key.startswith("OKTA_"):
            monkeypatch.delenv(key, raising=False)
