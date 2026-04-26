"""Shared fixtures for engine unit tests."""

from pathlib import Path

import pytest

from engine.compliance.india import ComplianceRules, load_rules

# Always load rules from the project-level rules/ directory
RULES_DIR = Path(__file__).parent.parent.parent / "rules"


@pytest.fixture(scope="session")
def maharashtra_rules() -> ComplianceRules:
    return load_rules("Maharashtra", rules_dir=RULES_DIR)


@pytest.fixture(scope="session")
def karnataka_rules() -> ComplianceRules:
    return load_rules("Karnataka", rules_dir=RULES_DIR)


@pytest.fixture(scope="session")
def delhi_rules() -> ComplianceRules:
    return load_rules("Delhi", rules_dir=RULES_DIR)
