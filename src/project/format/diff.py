from collections.abc import Iterable
from itertools import groupby
from pathlib import Path
from typing import Self, TextIO
from warnings import deprecated

from pydantic import BaseModel


class Change(BaseModel):
    file: Path = Path()
    line: int = 0
    lines: list[str] = []


@deprecated("Experimental")
class Diff(BaseModel):
    old: Change
    new: Change

    @classmethod
    def dump(cls, diff: dict[Path, list[Self]], *, context: int = 0) -> str:
        for file, hunks in diff.items():
            pass

    @classmethod
    def parse(cls, text: TextIO) -> dict[Path, list[Self]]:
        """Parse a diff into change sets.

        .. code-block:: diff

           --- /home/Projects/cxx/firmware/CMakeLists.txt
           +++ /home/Projects/cxx/firmware/CMakeLists.txt
           @@ -10,11 +10,11 @@
            add_subdirectory(external SYSTEM EXCLUDE_FROM_ALL)
            add_executable(firmware.main "src/firmware/main.cxx")
            target_link_libraries(firmware.main PRIVATE firmware.hal)
            target_link_options(
              firmware.main
           -   PRIVATE
           +  PRIVATE
                -T
                "${CMAKE_CURRENT_LIST_DIR}/src/firmware/STM32F429xx_FLASH.ld"

        Args:
            text: Diff text

        Returns:
            Hunks grouped by file.
        """
        return {k: list(v) for k, v in groupby(cls._parse(text), key=lambda d: d.old.file)}

    @classmethod
    def _parse(cls, text: TextIO) -> Iterable[Self]:
        first_file = True
        first_hunk_in_file = True
        lines_seen = False

        old = Change()
        new = Change()

        for line in text:
            if line.startswith("--- "):
                # Use "---" as an anchor to determine when the next file has started
                if not first_file:
                    yield cls(old=old, new=new)
                    old, new = Change(), Change()
                first_file = False
                first_hunk_in_file = True
                lines_seen = False

                # "--- a/path/to/file.txt" -> "path/to/file.txt"
                path = line[len("--- ") :].rstrip("\r\n")
                if path[1] == "/":
                    path = path[2:]
                old.file = Path(path)

            elif line.startswith("+++ "):
                # "+++ b/path/to/file.txt" -> "path/to/file.txt"
                path = line[len("+++ ") :].rstrip("\r\n")
                if path[1] == "/":
                    path = path[2:]
                new.file = Path(path)

            elif line.startswith("@@"):
                # Multiple "@@"-delimited hunks can appear within one file's diff lines
                if not first_hunk_in_file:
                    yield cls(old=old, new=new)
                    old, new = Change(file=old.file), Change(file=new.file)
                first_hunk_in_file = False
                lines_seen = False

                # "@@ -10,11 +10,11 @@" -> [-10, 11, 10, 11]
                tokens = line.strip("@ \r\n").replace(" ", ",").split(",")
                old.line, _, new.line, _ = (int(e) for e in tokens)
                old.line = -old.line

            elif line.startswith("-"):
                # Lines that start with - are deletions
                old.lines.append(line[len("-") :])
                lines_seen = True

            elif line.startswith("+"):
                # Lines that start with + are insertions
                new.lines.append(line[len("+") :])
                lines_seen = True

            elif not lines_seen:
                old.line += 1
                new.line += 1

        # There is no final "---" to use as an anchor
        yield cls(old=old, new=new)
