"""Project output directories.

These remain rooted to the project's base directory. This allows us to definitively know where our outputs are::

   .artifacts/
   |-- logs/
   |-- html/
   |-- docs/
   |-- install/
   `-- stage/
       |-- lint/
       |-- test/
       `-- cov/
"""

from functools import cache
from pathlib import Path


@cache
def project_dir() -> Path:
    current = Path.cwd()
    root = current.root
    while current != root:
        git = current / ".git"
        if git.is_dir() or (git.is_file() and "worktrees" in git.read_text()):
            return current
        current = current.parent
    return Path.cwd()


def cache_dir(subdir: str = "") -> Path:
    path = project_dir() / ".cache"
    if subdir:
        path = path / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_dir() -> Path:
    path = project_dir() / ".build"
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_dir() -> Path:
    path = project_dir() / ".artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def install_dir() -> Path:
    path = artifact_dir() / "install"
    path.mkdir(parents=True, exist_ok=True)
    return path


def docs_dir() -> Path:
    path = artifact_dir() / "docs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = artifact_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def html_dir() -> Path:
    path = artifact_dir() / "html"
    path.mkdir(parents=True, exist_ok=True)
    return path


def stage_dir() -> Path:
    path = artifact_dir() / "stage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_stage_dir() -> Path:
    path = artifact_dir() / "build"
    path.mkdir(parents=True, exist_ok=True)
    return path


def lint_stage_dir() -> Path:
    path = stage_dir() / "lint"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_stage_dir() -> Path:
    path = stage_dir() / "test"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cov_stage_dir() -> Path:
    path = stage_dir() / "cov"
    path.mkdir(parents=True, exist_ok=True)
    return path
