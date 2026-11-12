"""CONCEPT:OK-OS.governance.okta Base client: rate limits, 429 backoff, errors, redaction."""

import time

import pytest

import okta_agent.api.api_client_base as base
from okta_agent.api.api_client_base import (
    OktaApiError,
    _after_cursor,
    drop_none,
    redact_secrets,
)
from tests.conftest import TEST_TOKEN, json_response


@pytest.fixture
def sleep_spy(monkeypatch):
    calls: list[float] = []
    monkeypatch.setattr(base.time, "sleep", lambda s: calls.append(s))
    return calls


@pytest.mark.concept("OK-OS.governance.okta")
class TestRateLimitAwareness:
    def test_rate_limit_headers_captured(self, make_api):
        api = make_api(lambda request: json_response({"id": "x"}))
        api.get_org()
        assert api.last_rate_limit == {
            "limit": 600,
            "remaining": 599,
            "reset": 1700000000,
        }

    def test_envelope_exposes_rate_limit(self, make_api):
        api = make_api(lambda request: json_response({"id": "x"}))
        result = api.get_org()
        assert result["rate_limit"]["remaining"] == 599

    def test_malformed_rate_limit_headers_ignored(self, make_api):
        api = make_api(
            lambda request: json_response(
                {"id": "x"},
                headers={"X-Rate-Limit-Remaining": "not-a-number"},
            )
        )
        api.get_org()
        assert "remaining" not in (api.last_rate_limit or {})
        assert api.last_rate_limit["limit"] == 600


@pytest.mark.concept("OK-OS.governance.okta")
class TestBackoffOn429:
    def test_retries_after_429_until_success(self, make_api, sleep_spy):
        state = {"n": 0}

        def handler(request):
            state["n"] += 1
            if state["n"] == 1:
                return json_response(
                    {"errorCode": "E0000047"},
                    status=429,
                    headers={"X-Rate-Limit-Reset": str(time.time() + 5)},
                )
            return json_response({"id": "ok"})

        api = make_api(handler)
        result = api.get_org()
        assert result["data"]["id"] == "ok"
        assert state["n"] == 2
        assert len(sleep_spy) == 1
        assert 1.0 <= sleep_spy[0] <= 6.0

    def test_backoff_capped(self, make_api, sleep_spy):
        state = {"n": 0}

        def handler(request):
            state["n"] += 1
            if state["n"] == 1:
                return json_response(
                    {},
                    status=429,
                    headers={"X-Rate-Limit-Reset": str(time.time() + 9999)},
                )
            return json_response({"id": "ok"})

        api = make_api(handler, backoff_cap=3.0)
        api.get_org()
        assert sleep_spy == [3.0]

    def test_backoff_floor_when_reset_in_past(self, make_api, sleep_spy):
        state = {"n": 0}

        def handler(request):
            state["n"] += 1
            if state["n"] == 1:
                return json_response(
                    {}, status=429, headers={"X-Rate-Limit-Reset": "1"}
                )
            return json_response({"id": "ok"})

        make_api(handler).get_org()
        assert sleep_spy == [1.0]

    def test_retries_exhausted_raises_429(self, make_api, sleep_spy):
        def handler(request):
            return json_response(
                {
                    "errorCode": "E0000047",
                    "errorSummary": "API call exceeded rate limit",
                },
                status=429,
                headers={"X-Rate-Limit-Reset": str(time.time() + 1)},
            )

        api = make_api(handler, max_retries=1)
        with pytest.raises(OktaApiError) as excinfo:
            api.get_org()
        assert excinfo.value.status == 429
        assert excinfo.value.error_code == "E0000047"
        assert len(sleep_spy) == 1


@pytest.mark.concept("OK-OS.governance.okta")
class TestErrorEnvelopeMapping:
    def test_okta_error_fields_mapped(self, make_api):
        def handler(request):
            return json_response(
                {
                    "errorCode": "E0000007",
                    "errorSummary": "Not found: Resource not found: u404 (User)",
                    "errorId": "oae123",
                    "errorCauses": [{"errorSummary": "cause"}],
                },
                status=404,
            )

        with pytest.raises(OktaApiError) as excinfo:
            make_api(handler).get_user("u404")
        err = excinfo.value.to_dict()
        assert err["status"] == 404
        assert err["error_code"] == "E0000007"
        assert err["error_summary"] == "Okta request failed"
        assert err["error_id"] is None
        assert err["error_causes"] == []
        assert err["rate_limit"]["limit"] == 600

    def test_non_json_error_body(self, make_api):
        import httpx

        def handler(request):
            return httpx.Response(502, text="Bad Gateway")

        with pytest.raises(OktaApiError) as excinfo:
            make_api(handler).get_org()
        assert excinfo.value.status == 502
        assert excinfo.value.error_summary is not None
        assert excinfo.value.error_summary == "Okta request failed"

    def test_204_maps_to_success(self, make_api):
        import httpx

        api = make_api(lambda request: httpx.Response(204))
        assert api.clear_user_sessions("u1")["data"] == {"status": "success"}


@pytest.mark.concept("OK-OS.identity.default")
class TestRedaction:
    def test_error_summary_redacts_credential(self, make_api):
        def handler(request):
            return json_response(
                {"errorSummary": f"Invalid token provided: {TEST_TOKEN}"},
                status=401,
            )

        with pytest.raises(OktaApiError) as excinfo:
            make_api(handler).get_org()
        assert excinfo.value.error_summary is not None
        assert TEST_TOKEN not in excinfo.value.error_summary
        assert excinfo.value.error_summary == "Okta request failed"

    def test_redact_secrets_scrubs_auth_schemes(self):
        text = "header was 'Authorization: SSWS abc123def' and 'Bearer xyz.token-1'"
        out = redact_secrets(text)
        assert "abc123def" not in out
        assert "xyz.token-1" not in out
        assert out.count("***REDACTED***") == 2

    def test_redact_secrets_scrubs_known_values(self):
        out = redact_secrets("leak: s3cr3t-value", ["s3cr3t-value"])
        assert out == "leak: ***REDACTED***"


@pytest.mark.concept("OK-OS.governance.okta")
class TestHelpers:
    def test_drop_none(self):
        assert drop_none({"a": 1, "b": None, "c": False}) == {"a": 1, "c": False}

    def test_after_cursor_extraction(self):
        url = "https://x.okta.com/api/v1/users?limit=2&after=00ucursor"
        assert _after_cursor(url) == "00ucursor"
        assert _after_cursor("https://x.okta.com/api/v1/users") is None
        assert _after_cursor(None) is None
