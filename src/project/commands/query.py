from typing import TYPE_CHECKING

from project.system.files import FileType
from project.tool.git import Git

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from pathlib import Path


def resolve_files(paths: Collection[Path]) -> Iterable[Path]:
    """Flattens a list of files, directories, and/or FileTypes into a list of existing files on disk.

    Args:
        paths: A list of files, directories, or FileType names (packed into a relative path).
        If empty, files changed since the last git ancestor are returned.

    Returns:
        Files matching the given paths.
    """
    git = Git()
    if not paths:
        yield from git.files_changed(from_base="main")

    seen: set[Path] = set()

    def unseen(paths: Iterable[Path]) -> Iterable[Path]:
        for path in paths:
            path = path.absolute()  # noqa: PLW2901
            if path not in seen:
                seen.add(path)
                yield path

    for path in paths:
        if path.is_file():
            yield from unseen([path])
        elif path.is_dir():
            yield from unseen(git.files(matching=[str(path / "*")]))
        elif ft := FileType.from_name(str(path)):
            yield from unseen(git.files(matching=ft.globs))
