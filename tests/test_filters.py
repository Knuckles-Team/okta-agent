"""CONCEPT:OK-OS.governance.okta-3 SCIM filter expression building."""

import pytest

from okta_agent.api.filters import build_filter, scim_clause, scim_value


@pytest.mark.concept("OK-OS.governance.okta-3")
class TestScimValue:
    def test_strings_quoted(self):
        assert scim_value("ACTIVE") == '"ACTIVE"'

    def test_embedded_quotes_escaped(self):
        assert scim_value('a"b') == '"a\\"b"'

    def test_backslashes_escaped(self):
        assert scim_value("a\\b") == '"a\\\\b"'

    def test_booleans_and_numbers(self):
        assert scim_value(True) == "true"
        assert scim_value(False) == "false"
        assert scim_value(7) == "7"


@pytest.mark.concept("OK-OS.governance.okta-3")
class TestScimClause:
    def test_binary_clause(self):
        assert scim_clause("status", "eq", "ACTIVE") == 'status eq "ACTIVE"'

    def test_pr_takes_no_value(self):
        assert scim_clause("profile.mobilePhone", "pr") == "profile.mobilePhone pr"

    def test_unknown_operator_rejected(self):
        with pytest.raises(ValueError, match="Unsupported SCIM operator"):
            scim_clause("status", "like", "x")

    def test_missing_value_rejected(self):
        with pytest.raises(ValueError, match="requires a value"):
            scim_clause("status", "eq")


@pytest.mark.concept("OK-OS.governance.okta-3")
class TestBuildFilter:
    def test_and_join(self):
        expr = build_filter(
            [
                {"field": "status", "op": "eq", "value": "ACTIVE"},
                {
                    "field": "lastUpdated",
                    "op": "gt",
                    "value": "2026-01-01T00:00:00.000Z",
                },
            ]
        )
        assert expr == (
            'status eq "ACTIVE" and lastUpdated gt "2026-01-01T00:00:00.000Z"'
        )

    def test_or_join(self):
        expr = build_filter(
            [
                {"field": "status", "op": "eq", "value": "STAGED"},
                {"field": "status", "op": "eq", "value": "PROVISIONED"},
            ],
            joiner="or",
        )
        assert expr == 'status eq "STAGED" or status eq "PROVISIONED"'

    def test_default_op_is_eq(self):
        assert build_filter([{"field": "id", "value": "u1"}]) == 'id eq "u1"'

    def test_bad_joiner_rejected(self):
        with pytest.raises(ValueError, match="Joiner"):
            build_filter([{"field": "a", "op": "eq", "value": 1}], joiner="xor")

    def test_empty_conditions_rejected(self):
        with pytest.raises(ValueError, match="At least one"):
            build_filter([])

    def test_injection_attempt_stays_quoted(self):
        expr = build_filter(
            [{"field": "profile.login", "op": "eq", "value": 'x" or status eq "ACTIVE'}]
        )
        assert expr == 'profile.login eq "x\\" or status eq \\"ACTIVE"'
