"""CONCEPT:OK-OS.governance.okta / CONCEPT:OK-OS.governance.okta-2 typed envelope and input-model contracts."""


import pytest

from okta_agent.api.api_client_base import OktaApiError
from okta_agent.okta_response_models import (
    ErrorEnvelope,
    RateLimitSnapshot,
    ResponseEnvelope,
)


@pytest.mark.concept("OK-OS.governance.okta")
class TestResponseModels:
    def test_envelope_parses_api_shape(self):
        envelope = ResponseEnvelope.model_validate(
            {
                "data": [{"id": "00u1"}],
                "rate_limit": {"limit": 600, "remaining": 599, "reset": 1700000000},
                "count": 1,
                "truncated": False,
                "next_cursor": None,
            }
        )
        assert envelope.count == 1
        assert isinstance(envelope.rate_limit, RateLimitSnapshot)
        assert envelope.rate_limit.remaining == 599

    def test_error_envelope_parses_okta_api_error(self):
        exc = OktaApiError(
            status=403,
            error_code="E0000006",
            error_summary="You do not have permission",
            error_id="oae123",
        )
        envelope = ErrorEnvelope.model_validate({"error": exc.to_dict()})
        assert envelope.error.status == 403
        assert envelope.error.error_code == "E0000006"

    def test_error_envelope_parses_destructive_gate_shape(self):
        envelope = ErrorEnvelope.model_validate(
            {
                "error": {
                    "message": "Action 'delete' is destructive and blocked by default.",
                    "destructive_actions": ["delete"],
                }
            }
        )
        assert envelope.error.destructive_actions == ["delete"]
