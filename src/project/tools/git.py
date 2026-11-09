# ruff: noqa: PTH110 - We use os.path.exists() because we're speed-sensitive here. Don't redundantly construct Paths.
import os
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from project.host.program import execute

if TYPE_CHECKING:
    from collections.abc import Iterable


class Git(BaseModel):
    """For interfacing with the project's git repository."""

    def project_files(self, *, matching: Iterable[str] | None = None) -> Iterable[Path]:
        """Get files from the project.

        Args:
            matching: Optional or'd glob filter(s).

        Returns:
            Files tracked by git (provided they exist) or those yet to be staged.
        """
        matching = list(matching or [])
        proc = execute("git", ["ls-files", "-z", "--cached", "--others", "--exclude-standard", *matching])
        return (Path(p) for p in proc.stdout.split("\0") if p and os.path.exists(p))

    def files_change_from_upstream(self, *, matching: Iterable[str] | None = None) -> Iterable[Path]:
        """Get files changed since the last common ancestor.

        Args:
            matching: Optional or'd glob filter(s).

        Returns:
            Files tracked by git (provided they exist) or those yet to be staged.
        """
        matching = list(matching or [])
        tracked_files = execute("git", ["diff", "-z", "--name-only", "@{upstream}...HEAD", *matching])
        new_files = execute("git", ["ls-files", "-z", "--others", "--exclude-standard", *matching])
        return chain(
            (Path(p) for p in tracked_files.stdout.split("\0") if p and os.path.exists(p)),
            (Path(p) for p in new_files.stdout.split("\0") if p and os.path.exists(p)),
        )
