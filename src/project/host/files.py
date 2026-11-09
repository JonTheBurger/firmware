from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import ClassVar, Final

CMAKE_EXTENSIONS: Final = ["CMakeLists.txt", ".cmake"]
CXX_SRC_EXTENSIONS: Final = [".cc", ".cpp", ".cxx"]
CXX_HEADER_EXTENSIONS: Final = [".hh", ".hpp", ".hxx"]
CXX_EXTENSIONS: Final = CXX_SRC_EXTENSIONS + CXX_HEADER_EXTENSIONS
PY_EXTENSIONS: Final = [".py"]


class Extensions(Enum):
    _value_ = list[str]

    CMAKE = CMAKE_EXTENSIONS
    CXX_SRC = CXX_SRC_EXTENSIONS
    CXX_HEADER = CXX_HEADER_EXTENSIONS
    CXX = CXX_EXTENSIONS
    PY = PY_EXTENSIONS
