# ruff: noqa: PTH110 - We use os.path.exists() because we're speed-sensitive here. Don't redundantly construct Paths.
import os
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field

from project.system.program import execute

if TYPE_CHECKING:
    from collections.abc import Iterable
    from subprocess import CompletedProcess


class Git(BaseModel):
    """For interfacing with the project's git repository."""

    cwd: Annotated[Path, Field(description="Current working directory to run git from")] = Path()

    @property
    def root(self) -> Path:
        """Gets the project root directory."""
        return Path(self.git(["rev-parse", "--show-toplevel"]).stdout.strip())

    @property
    def dir(self) -> Path:
        """Gets the .git directory."""
        return Path(self.git(["rev-parse", "--git-dir"]).stdout.strip())

    def git(self, args: Iterable[str]) -> CompletedProcess[str]:
        """Run a git command."""
        return execute("git", ["-C", str(self.cwd), *args])

    def files(self, *, matching: Iterable[str] | None = None) -> Iterable[Path]:
        """Get files from the project.

        Args:
            matching: Optional or'd glob filter(s).

        Returns:
            Files tracked by git (provided they exist) or those yet to be staged.
        """
        matching = list(matching or [])
        proc = self.git(["ls-files", "-z", "--cached", "--others", "--exclude-standard", *matching])
        return (Path(p) for p in proc.stdout.split("\0") if p and os.path.exists(p))

    def files_changed(self, *, matching: Iterable[str] | None = None, from_base: str = "HEAD~1") -> Iterable[Path]:
        """Get files changed since the last common ancestor.

        Args:
            matching: Optional or'd glob filter(s).

        Returns:
            Files tracked by git (provided they exist) or those yet to be staged.
        """
        matching = list(matching or [])
        tracked_files = self.git(["diff", "-z", "--name-only", "--diff-filter=AM", f"{from_base}...HEAD", *matching])
        new_files = self.git(["ls-files", "-z", "--others", "--exclude-standard", *matching])
        return chain(
            (Path(p) for p in tracked_files.stdout.split("\0") if p and os.path.exists(p)),
            (Path(p) for p in new_files.stdout.split("\0") if p and os.path.exists(p)),
        )
