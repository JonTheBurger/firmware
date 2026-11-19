from typing import TYPE_CHECKING, Final

import pytest

from project.util.file_range import FilePos, FileRange

if TYPE_CHECKING:
    from pathlib import Path


_EXAMPLE: Final = """\
Hello World
1234567890
abcdefghijklmnopqrstuvwxyz
"""


@pytest.fixture
def example(tmp_path: Path) -> Path:
    example_txt = tmp_path / "example.txt"
    example_txt.write_text(_EXAMPLE)
    return example_txt


def test_read_lines(example: Path) -> None:
    """When inclusive line bounds of file are read, Then all lines returned."""
    extent = FileRange(example, 1, 3)
    lines = list(extent.read_lines())
    assert lines == [
        "Hello World",
        "1234567890",
        "abcdefghijklmnopqrstuvwxyz",
    ]


def test_read_lines_column_offsets(example: Path) -> None:
    """When ranges with columns are supplied, Then only the inclusive bounds of the text are returned."""
    extent = FileRange(example, (2, 5), (3, 8))
    lines = list(extent.read_lines())
    assert lines == [
        "567890",
        "abcdefgh",
    ]


def test_read_lines_beyond_lines(example: Path) -> None:
    """When reading lines past the original document, Then the read truncates to available lines."""
    extent = FileRange(example, 1, 10)
    lines = list(extent.read_lines())
    assert lines == [
        "Hello World",
        "1234567890",
        "abcdefghijklmnopqrstuvwxyz",
    ]


def test_read_lines_beyond_columns(example: Path) -> None:
    """When reading columns past the original document, Then the read truncates to available lines."""
    extent = FileRange(example, 1, (1, 50))
    lines = list(extent.read_lines())
    assert lines == ["Hello World"]


def test_read_text(example: Path) -> None:
    """When reading all text, Then original text returned."""
    extent = FileRange(example, 1, 3)
    assert extent.read_text() == _EXAMPLE


def test_read_one_line(example: Path) -> None:
    """When reading one line of text, Then only the text within column limits is returned."""
    extent = FileRange(example, (2, 7), (2, 9))
    assert extent.read_text() == "789"


def test_read_one_line_to_end(example: Path) -> None:
    """When reading one line with an unspecified end column, Then the remaining line is returned."""
    extent = FileRange(example, (2, 7), 2)
    assert extent.read_text() == "7890\n"


def test_file_pos_from_string() -> None:
    """When parsing a <file>:<line>:<col> with a Windows drive, Then the drive is preserved."""
    assert FilePos.from_str(r"C:\Users\Alice\main.c:3:2") == FilePos(file=r"C:\Users\Alice\main.c", line=3, column=2)
    assert FilePos.from_str(r"C:\Users\Alice\main.c:3") == FilePos(file=r"C:\Users\Alice\main.c", line=3)
