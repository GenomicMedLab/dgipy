"""Provide basic test configuration and fixture root."""
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir():
    """Provide path to fixtures directory."""
    return Path(__file__).resolve().parent / "fixtures"
