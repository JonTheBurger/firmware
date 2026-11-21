import re
from collections.abc import Collection
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Self

from project.format.sarif import (
    Sarif,
    SarifResult,
    SarifRun,
)
from project.system.program import Program

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class FormatResult:
    """Ruff format result."""

    reformatted: int = 0
    unchanged: int = 0

    @classmethod
    def from_stdout(cls, stdout: str) -> Self:
        return cls(
            reformatted=int((re.search(r"(\d+) files? reformatted", stdout) or ["", "0"])[1]),
            unchanged=int((re.search(r"(\d+) files? left unchanged", stdout) or ["", "0"])[1]),
        )


@dataclass(frozen=True, slots=True)
class FixResult:
    """Ruff fix result."""

    fixed: int = 0
    available: int = 0

    @classmethod
    def from_stdout(cls, stdout: str) -> Self:
        return cls(
            fixed=int((re.search(r"Fixed (\d+) error", stdout) or ["", "0"])[1]),
            available=int((re.search(r"(\d+) additional fix(?:es)? available", stdout) or ["", "0"])[1]),
        )


class Ruff(Program):
    uri: ClassVar[str] = "https://github.com/astral-sh/ruff"

    # --stdin-filename
    def fix(self, files: Iterable[Path]) -> FixResult:
        proc = self.execute(["check", "--fix", "--fix-only", "--", *files])
        return FixResult.from_stdout(proc.stdout or "")

    def check(self, files: Collection[Path]) -> Sarif:
        proc = self.execute(["check", "--exit-zero", "--output-format=sarif", "--", *files])
        return self._parse_sarif(proc.stdout or "", files)

    def format(self, files: Iterable[Path]) -> FormatResult:
        proc = self.execute(["format", "--", *files])
        return FormatResult.from_stdout(proc.stdout or "")

    def format_check(self, files: Collection[Path]) -> Sarif:
        proc = self.execute(["format", "--check", "--exit-zero", "--output-format=sarif", "--", *files], check=False)
        return self._parse_sarif(proc.stdout or "", files)

    def _parse_sarif(self, stdout: str, files: Iterable[Path]) -> Sarif:
        if stdout:
            sarif = Sarif.model_validate_json(stdout)
            if not sarif.runs[-1].results:
                sarif.runs[-1].results = [SarifResult.success(file) for file in files]
            return sarif
        return Sarif(
            runs=[
                SarifRun(
                    results=[SarifResult.success(file) for file in files],
                    tool=self.sarif(),
                )
            ]
        )
