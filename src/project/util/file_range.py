"""Library for reading a subset of a file, or constructing / parsing ``<file>:<line>:<col>`` diagnostics."""

from functools import total_ordering
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Self, overload

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from collections.abc import Iterable

type LineColumnType = LineCol | tuple[int, int] | int
"""Any type that can be coerced into a :class:`LineCol`."""


@total_ordering
class LineCol(BaseModel):
    """Line + optional column pairing."""

    line: Annotated[int, Field(description="1-indexed", gt=0)] = 1
    column: Annotated[int, Field(description="1-indexed, 0 is used as a sentinel to mean the full line", ge=0)] = 0

    @property
    def y(self) -> int:
        """Zero-offset version of line."""
        return self.line - 1

    @property
    def x(self) -> int | None:
        """Zero-offset version of column. None if column was unset."""
        return self.column - 1 if self.column else None

    @property
    def end(self) -> int | None:
        """Slice index for column."""
        return self.column or None

    @overload
    def __init__(self, line: LineCol, **kwargs: Any) -> None: ...

    @overload
    def __init__(self, line: tuple[int, int], **kwargs: Any) -> None: ...

    @overload
    def __init__(self, line: int, column: int = 0, **kwargs: Any) -> None: ...

    def __init__(self, line: LineColumnType, column: int = 0, **kwargs: Any) -> None:
        """Create a Line + Column pair.

        Args:
            line: An int line number, a ``tuple[line: int, column: int]`` pair, or an instance of :class:`LineCol`.
            column: Column number, starting at 1, when ``line`` is supplied. ``0`` means the whole line (default).
        """
        if isinstance(line, LineCol):
            super().__init__(line=line.line, column=line.column, **kwargs)
        elif isinstance(line, tuple):
            super().__init__(line=line[0], column=line[1], **kwargs)
        else:
            super().__init__(line=line, column=column, **kwargs)

    def __str__(self) -> str:
        """Format of ``<line>:<column>`` (column omitted if 0)."""
        return f"{self.line}:{self.column}" if self.column else str(self.line)

    def __hash__(self) -> int:
        return hash((self.line, self.column))

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, LineCol):
            return False
        return self.line == other.line and self.column == other.column

    def __lt__(self, other: Self) -> bool:
        return (self.line, self.column) < (other.line, other.column)


class FilePos(LineCol):
    """A ``<file>:<line>:<column>``."""

    file: Path

    def __str__(self) -> str:
        """Format of ``<file>:<line>:<column>`` (column omitted if 0)."""
        return f"{self.file}:{super().__str__()}"

    @classmethod
    def from_str(cls, string: str) -> Self:
        """Parse from a ``<file>:<line>:<column>`` (column optional)."""
        tokens = string[len("C:") :].split(":")
        if len(tokens) == 3:  # noqa: PLR2004 - <file>:<line>:<col>
            return cls(file=f"{string[: len('C:')]}{tokens[0]}", line=int(tokens[1]), column=int(tokens[2]))
        if len(tokens) == 2:  # noqa: PLR2004 - <file>:<line>
            return cls(file=f"{string[: len('C:')]}{tokens[0]}", line=int(tokens[1]))
        raise ValueError("Invalid string format")


class FileRange(BaseModel):
    """A range of text within a single file."""

    file: Path
    start: Annotated[LineCol, Field(description="Inclusive beginning of range. 0 column = start of line.")]
    finish: Annotated[LineCol, Field(description="Inclusive end of range. Must be >= start. 0 column = end of line.")]

    def __init__(
        self,
        file: Path | str,
        start: LineColumnType,
        finish: LineColumnType | None = None,
        **kwargs: Any,
    ) -> None:
        start = LineCol(start)
        finish = LineCol(finish or start.model_copy())
        super().__init__(file=Path(file), start=start, finish=finish, **kwargs)

    @model_validator(mode="after")
    def __model_validator_after(self) -> Self:
        if self.start.line > self.finish.line:
            raise ValueError("Requires: start.line <= finish.line")
        if self.start.line == self.finish.line and self.start.column > self.finish.column and self.finish.column != 0:
            raise ValueError("Requires: start.column <= finish.column")
        return self

    def __str__(self) -> str:
        """Format of ``<file>:<start-line>:<start-col>-<finish-line>:<finish-col>."""
        if self.finish <= self.start:
            return f"{self.file}:{self.start}"
        return f"{self.file}:{self.start}-{self.finish}"

    def read_text(self) -> str:
        """String containing the referenced text. Lines/Columns beyond file bounds are truncated."""
        return "".join(self.read_lines(keepends=True))

    def read_lines(self, *, keepends: bool = False) -> Iterable[str]:
        """Lines of the referenced text. Lines/Columns beyond file bounds are truncated.

        Args:
            keepends: When ``True``, ``"\r" and "\n"`` are removed (``False`` by default).

        Returns:
            Lines of text.
        """
        start, finish = self.start, self.finish
        last_line = finish.line - start.line + 1

        with self.file.open("r", encoding="utf-8") as f:
            lines = islice(f, start.line - 1, finish.line)
            lines = [eol if keepends else eol.rstrip("\r\n") for eol in lines]

        if not lines:
            return lines

        if len(lines) == last_line:
            lines[-1] = lines[-1][: finish.end]

        lines[0] = lines[0][start.x :]
        return lines
