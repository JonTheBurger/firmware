import pytest

from project.tools.ruff import Ruff


@pytest.mark.integration
def test_ruff() -> None:
    ruff = Ruff.tool()
    assert ruff.name == "ruff"
    assert ruff.version
