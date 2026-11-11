from typing import TYPE_CHECKING

from project.system.files import FileType
from project.system.program import execute
from project.tool.git import Git

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def lint(files: Iterable[Path]) -> None:
    """Runs static analysis on source files."""
    categorized = FileType.categorize(files)

    if py_files := categorized.get(FileType.PY):
        lint_py(py_files)
    if cmake_files := categorized.get(FileType.CMAKE):
        lint_cmake(cmake_files)
    if cxx_files := categorized.get(FileType.CXX):
        lint_cxx(cxx_files)


def lint_py(files: Iterable[Path]) -> None:
    # --stdin-filename
    execute("ruff", ["format", "--check", "--", *files], check=False, capture=False)
    execute("ruff", ["check", "--", *files], check=False, capture=False)


def lint_cmake(files: Iterable[Path]) -> None:
    # --stdin-filepath
    cache_dir = Git().root / ".cache/gersemi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    execute(
        "gersemi",
        ["--check", "--cache", "--cache-dir", cache_dir, "--respect-ignore-files", "--", *files],
        check=False,
        capture=False,
    )


def lint_cxx(files: Iterable[Path]) -> None:
    # --files or @<file>
    execute(
        "clang-format",
        ["--Werror", "--dry-run", "--fail-on-incomplete-format", "--", *files],
        check=False,
        capture=False,
    )
    execute("clang-tidy", [*files], check=False, capture=False)
