from collections.abc import Iterable
from pathlib import Path

from project.format.sarif import Sarif
from project.system.program import Program


class Ruff(Program):
    def format(self, files: Iterable[Path]) -> Sarif | None:
        proc = self.execute(["format", "--output-format=sarif", "--", *files])
        if proc.stdout:
            return Sarif.model_validate_json(proc.stdout)
        return None

    def check(self, files: Iterable[Path]) -> Sarif | None:
        proc = self.execute(["check", "--output-format=sarif", "--fix", "--fix-only", "--", *files])
        if proc.stdout:
            return Sarif.model_validate_json(proc.stdout)
        return None
