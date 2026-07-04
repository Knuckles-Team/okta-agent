"""Concept traceability: every CONCEPT marker in code is registered in docs."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER_RE = re.compile(r"CONCEPT:([A-Z]+-[\d.]+)")


def _markers_in(path: Path) -> set[str]:
    found: set[str] = set()
    for file in path.rglob("*.py"):
        found.update(MARKER_RE.findall(file.read_text()))
    return found


@pytest.mark.concept("OK-OS.governance.okta")
def test_all_code_concepts_registered_in_docs():
    code_concepts = _markers_in(REPO_ROOT / "okta_agent")
    assert code_concepts, "expected CONCEPT markers in source"
    registry = (REPO_ROOT / "docs" / "concepts.md").read_text()
    registered = set(MARKER_RE.findall(registry))
    missing = code_concepts - registered
    assert not missing, f"CONCEPT markers missing from docs/concepts.md: {missing}"


@pytest.mark.concept("OK-OS.governance.okta")
def test_expected_concepts_present():
    code_concepts = _markers_in(REPO_ROOT / "okta_agent")
    for concept in ("OK-OS.governance.okta", "OK-OS.identity.okta", "OK-OS.governance.okta-2", "OK-OS.identity.default", "OK-OS.governance.okta-3"):
        assert concept in code_concepts
