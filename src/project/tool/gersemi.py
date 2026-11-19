from collections.abc import Iterable
from pathlib import Path

from project.format.sarif import Sarif
from project.system.program import Program
from project.tool.git import Git


class Gersemi(Program):
    @property
    def cache_dir(self) -> Path:
        cache_dir = Git.find().root / ".cache/gersemi"
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
