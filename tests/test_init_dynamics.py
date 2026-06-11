"""Dynamic facade exposure from the package root."""

import pytest


@pytest.mark.concept("OKTA-1.1")
def test_core_api_exposed_at_root():
    import okta_agent

    assert hasattr(okta_agent, "Api")
    assert "Api" in dir(okta_agent)


@pytest.mark.concept("OKTA-1.1")
def test_unknown_attribute_raises():
    import okta_agent

    with pytest.raises(AttributeError):
        _ = okta_agent.does_not_exist
