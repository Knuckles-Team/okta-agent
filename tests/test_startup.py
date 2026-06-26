"""Package import and version sanity."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.concept("OKTA-1.3")
def test_startup():
    import okta_agent

    assert re.match(r"^\d+\.\d+\.\d+", okta_agent.__version__)


@pytest.mark.concept("OKTA-1.3")
def test_pyproject_version_matches_package():
    import okta_agent

    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert match
    assert match.group(1) == okta_agent.__version__
