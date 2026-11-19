# ruff: noqa: PTH110 - We use os.path.exists() because we're speed-sensitive here. Don't redundantly construct Paths.
import os
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, override

from pydantic import Field

from project.core.units import Duration
from project.system.program import Program

if TYPE_CHECKING:
    from collections.abc import Iterable
    from subprocess import CompletedProcess


class Git(Program):
    """For interfacing with the project's git repository."""

    cwd: Annotated[Path, Field(description="Current working directory to run git from")] = Path()

    @property
    def root(self) -> Path:
        """Gets the project root directory."""
        return Path(self.execute(["rev-parse", "--show-toplevel"]).stdout.strip())

    @property
    def dir(self) -> Path:
        """Gets the .git directory."""
        return Path(self.execute(["rev-parse", "--git-dir"]).stdout.strip())

    @override
    def execute(
        self, args: Iterable[Any] | None, *, check: bool = True, capture: bool = True, timeout: Duration | None = None
    ) -> CompletedProcess[str]:
        """Run a git command."""
        return super().execute(["-C", str(self.cwd), *(args or [])], check=check, capture=capture, timeout=timeout)

    def files(self, *, matching: Iterable[str] | None = None) -> Iterable[Path]:
        """Get files from the project.

        Args:
            matching: Optional or'd glob filter(s).

        Returns:
            Files tracked by git (provided they exist) or those yet to be staged.
        """
        matching = list(matching or [])
        proc = self.execute(["ls-files", "-z", "--cached", "--others", "--exclude-standard", *matching])
        return (Path(p) for p in proc.stdout.split("\0") if p and os.path.exists(p))

    def files_changed(self, *, matching: Iterable[str] | None = None, from_base: str = "HEAD~1") -> Iterable[Path]:
        """Get files changed since the last common ancestor.

        Args:
            matching: Optional or'd glob filter(s).

        Returns:
            Files tracked by git (provided they exist) or those yet to be staged.
        """
        matching = list(matching or [])
        tracked_files = self.execute(
            ["diff", "-z", "--name-only", "--diff-filter=AM", f"{from_base}...HEAD", *matching]
        )
        new_files = self.execute(["ls-files", "-z", "--others", "--exclude-standard", *matching])
        return chain(
            (Path(p) for p in tracked_files.stdout.split("\0") if p and os.path.exists(p)),
            (Path(p) for p in new_files.stdout.split("\0") if p and os.path.exists(p)),
        )
