from pathlib import Path

import pytest


@pytest.fixture
def test_data() -> Path:
    """Access the test data directory."""
    return Path(__file__).parent / "data"
