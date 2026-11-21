from typing import TYPE_CHECKING

from project.system.files import FileType
from project.system.program import execute
from project.tool.git import Git
from project.tool.ruff import Ruff

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def fmt(files: Iterable[Path]) -> None:
    """Reformats source files."""
    categorized = FileType.categorize(files)

    if py_files := categorized.get(FileType.PY):
        fmt_py(py_files)
    if cmake_files := categorized.get(FileType.CMAKE):
        fmt_cmake(cmake_files)
    if cxx_files := categorized.get(FileType.CXX):
        fmt_cxx(cxx_files)


def fmt_py(files: Iterable[Path]) -> None:
    ruff = Ruff.tool()
    ruff.format(files)
    ruff.check(files)


def fmt_cmake(files: Iterable[Path]) -> None:
    # --stdin-filepath
    cache_dir = Git.tool().root / ".cache/gersemi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    execute(
        "gersemi",
        ["--in-place", "--cache", "--cache-dir", cache_dir, "--respect-ignore-files", "--", *files],
    )


def fmt_cxx(files: Iterable[Path]) -> None:
    # --files or @<file>
    execute("clang-format", ["-i", "--", *files])
