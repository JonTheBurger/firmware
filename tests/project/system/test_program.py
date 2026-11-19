import pytest

from project.tool.ruff import Ruff


@pytest.mark.integration
def test_ruff() -> None:
    ruff = Ruff.find()
    assert ruff.name == "ruff"
    assert ruff.version
