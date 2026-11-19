from pathlib import Path

from project.format.sarif import Sarif


def test_sarif(test_data: Path) -> None:
    file = test_data / "ruff.sarif.json"

    sarif = Sarif.model_validate_json(file.read_bytes())

    assert sarif.runs
    assert sarif.version

    run = sarif.runs[0]
    # pyrefly: ignore[missing-attribute]
    assert run.tool.driver.name == "ruff"

    result = run.results[0]
    assert result.level == "error"
