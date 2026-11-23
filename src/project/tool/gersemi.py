from typing import TYPE_CHECKING

from project.format.sarif import Sarif
from project.system.program import Program
from project.tool.git import Git

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class Gersemi(Program):
    @property
    def cache_dir(self) -> Path:
        cache_dir = Git.tool().root / ".cache/gersemi"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def format(self, files: Iterable[Path]) -> Sarif | None:
        proc = self.execute(
            ["--in-place", "--cache", "--cache-dir", self.cache_dir, "--respect-ignore-files", "--", *files]
        )
        if proc.stdout:
            return Sarif.model_validate_json(proc.stdout)
        return None

    def check(self, files: Iterable[Path]) -> Sarif | None:
        proc = self.execute(
            ["--check", "--cache", "--cache-dir", self.cache_dir, "--respect-ignore-files", "--", *files]
        )
        if proc.stdout:
            return Sarif.model_validate_json(proc.stdout)
        return None
