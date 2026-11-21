from project.format.report import InfoItem
from project.format.report import Report
from collections.abc import Collection
from typing import TYPE_CHECKING

from project.core.dirs import lint_dir
from project.format.report import Diagnostic
from project.system.files import FileType
from project.system.program import execute
from project.tool.git import Git
from project.tool.ruff import Ruff

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


def lint_py(files: Collection[Path]) -> None:
    diagnostics: list[Diagnostic] = []

    sarif = Ruff.tool().check(files)
    sarif.to_file(lint_dir() / "ruff.sarif")
    diagnostics.extend(Diagnostic.from_sarif(sarif))

    sarif = Ruff.tool().format_check(files)
    sarif.to_file(lint_dir() / "format.ruff.sarif")
    diagnostics.extend(Diagnostic.from_sarif(sarif))

    report = Report(
        title="Ruff Linter Results",
        diagnostics=diagnostics,
        info=[
            InfoItem(
                icon=":)",
                heading="COOL",
                message="Poggers",
            )
        ],
    )
    report.render()


def lint_cmake(files: Collection[Path]) -> None:
    # --stdin-filepath
    cache_dir = Git.tool().root / ".cache/gersemi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    execute(
        "gersemi",
        ["--check", "--cache", "--cache-dir", cache_dir, "--respect-ignore-files", "--", *files],
        check=False,
        capture=False,
    )


def lint_cxx(files: Collection[Path]) -> None:
    # --files or @<file>
    execute(
        "clang-format",
        ["--Werror", "--dry-run", "--fail-on-incomplete-format", "--", *files],
        check=False,
        capture=False,
    )
    execute("clang-tidy", [*files], check=False, capture=False)
