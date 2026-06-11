"""CONCEPT:OKTA-1.1 / CONCEPT:OKTA-1.3 typed envelope and input-model contracts."""

import json

import pytest
from pydantic import ValidationError

from okta_agent.api.api_client_base import OktaApiError
from okta_agent.okta_input_models import (
    AppCreateInput,
    FilterCondition,
    GroupMemberInput,
    PolicyListInput,
    SearchInput,
    SystemLogInput,
    UserCreateInput,
)
from okta_agent.okta_response_models import (
    ErrorEnvelope,
    RateLimitSnapshot,
    ResponseEnvelope,
)


@pytest.mark.concept("OKTA-1.3")
class TestInputModels:
    def test_search_input_round_trips_to_params_json(self):
        model = SearchInput(
            conditions=[FilterCondition(field="status", op="eq", value="ACTIVE")]
        )
        params = json.loads(model.model_dump_json(exclude_none=True))
        assert params["conditions"] == [
            {"field": "status", "op": "eq", "value": "ACTIVE"}
        ]
        assert params["joiner"] == "and"

    def test_user_create_requires_profile(self):
        with pytest.raises(ValidationError):
            UserCreateInput.model_validate({})
        assert UserCreateInput(profile={"login": "a@b.com"}).activate is True

    def test_group_member_input_matches_tool_param_keys(self):
        model = GroupMemberInput(group_id="00g1", user_id="00u1")
        assert model.model_dump() == {"group_id": "00g1", "user_id": "00u1"}

    def test_app_create_defaults_empty_settings(self):
        model = AppCreateInput(template="oidc", label="My App")
        assert model.settings == {}

    def test_policy_list_requires_policy_type(self):
        with pytest.raises(ValidationError):
            PolicyListInput.model_validate({})

    def test_system_log_input_is_fully_optional(self):
        assert SystemLogInput().model_dump(exclude_none=True) == {}


@pytest.mark.concept("OKTA-1.1")
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
