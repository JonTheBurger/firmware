from typing import TYPE_CHECKING

from project.commands.fmt import fmt_cmake, fmt_cxx, fmt_py
from project.system.files import FileType
from project.system.program import execute

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def fix(files: Iterable[Path]) -> None:
    """Fixes all auto-fixable problems."""
    categorized = FileType.categorize(files)

    if py_files := categorized.get(FileType.PY):
        fix_py(py_files)
    if cmake_files := categorized.get(FileType.CMAKE):
        fix_cmake(cmake_files)
    if cxx_files := categorized.get(FileType.CXX):
        fix_cxx(cxx_files)


def fix_py(files: Iterable[Path]) -> None:
    fmt_py(files)


def fix_cmake(files: Iterable[Path]) -> None:
    fmt_cmake(files)


def fix_cxx(files: Iterable[Path]) -> None:
    fmt_cxx(files)
    # -p BUILD_DIR
    execute("clang-tidy", ["--fix", *files])
