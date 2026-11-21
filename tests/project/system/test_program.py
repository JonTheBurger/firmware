import pytest

from project.tool.ruff import Ruff


@pytest.mark.integration
def test_ruff() -> None:
    ruff = Ruff.tool()
    assert ruff.name == "ruff"
    assert ruff.version
