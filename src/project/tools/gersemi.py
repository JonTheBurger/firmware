from typing import TYPE_CHECKING

from project.core.dirs import cache_dir
from project.formats.sarif import Sarif
from project.tools.tool import Tool

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class Gersemi(Tool):
    @property
    def cache_dir(self) -> Path:
        return cache_dir("gersemi")

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
