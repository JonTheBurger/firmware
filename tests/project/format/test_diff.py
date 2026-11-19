from pathlib import Path

from project.format.diff import Diff


def test_diff(test_data: Path) -> None:
    file = test_data / "gersemi.diff"
    with file.open() as f:
        diffs = Diff.parse(f)

    assert len(diffs) == 2

    hunks = diffs[Path("/home/user/Projects/cxx/firmware/CMakeLists.txt")]
    assert hunks[0].old.line == 15
    assert hunks[1].new.line == 29

    hunks = diffs[Path("/home/user/Projects/cxx/firmware/tools/cmake/toolchain/firmware.cmake")]
    assert hunks[0].old.line == 3
