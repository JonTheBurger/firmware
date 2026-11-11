from collections import defaultdict
from enum import Enum
from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping
    from pathlib import Path


class _FileTypeInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    extensions: frozenset[str] = Field(default_factory=frozenset)
    subtypes: frozenset[_FileTypeInfo] = Field(default_factory=frozenset)

    @model_validator(mode="before")
    @classmethod
    def _inherit_subtype_extensions(cls, data: Any) -> Any:
        subtypes: Iterable[_FileTypeInfo]
        if subtypes := data.get("subtypes"):
            extensions: Iterable[str] = data.get("extensions") or []
            data["extensions"] = frozenset((*extensions, *(*t.extensions for t in subtypes)))
        return data


class FileType(Enum):
    """File types known by this project.

    These file types are deemed to be relevant for project tooling, such as formatters and code generators.
    """

    CXX_HEADER_INL = _FileTypeInfo(name=":cxx.header.inl", extensions=[".inl", ".tpp", ".txx"])
    CXX_HEADER = _FileTypeInfo(name=":cxx.header", extensions=[".hh", ".hpp", ".hxx"], subtypes=[CXX_HEADER_INL])
    CXX_SOURCE = _FileTypeInfo(name=":cxx.source", extensions=[".cc", ".cpp", ".cxx"])
    CXX_MODULE = _FileTypeInfo(name=":cxx.module", extensions=[".cppm", ".ccm", ".cxxm", ".ixx"])
    CXX = _FileTypeInfo(name=":cxx", subtypes=[CXX_HEADER, CXX_SOURCE, CXX_MODULE])
    C_HEADER = _FileTypeInfo(name=":c.header", extensions=[".h"])
    C_SOURCE = _FileTypeInfo(name=":c.source", extensions=[".c"])
    C = _FileTypeInfo(name=":c", subtypes=[C_HEADER, C_SOURCE])
    CMAKE = _FileTypeInfo(name=":cmake", extensions=["CMakeLists.txt", ".cmake"])
    PY = _FileTypeInfo(name=":py", extensions=[".py"])
    ALL = _FileTypeInfo(name=":all", extensions=[""])

    @classmethod
    def from_name(cls, name: str) -> Self | None:
        """Lookup a file type by its colon alias, for example ``:c``."""
        try:
            return cls[name.lstrip(":*.").upper().replace(".", "_")]
        except KeyError:
            return None

    @classmethod
    def detect(cls, path: Path | str, *, subtypes: bool = False) -> FileType | None:
        """Finds the most specific known file type that matches path.

        Consider ``FileType.detect(path) or FileType.ALL``

        Args:
            path: Path to deduce.
            subtypes: If True, the most specific matching subtype will be returned, othewise use the general subtype.

        Returns:
            The matching file type, or None if the type was not known.
        """
        for filetype in cls:
            if filetype == FileType.ALL:
                continue
            if not subtypes and "." in filetype.name:
                continue
            if filetype.matches(path):
                return filetype
        return None

    @classmethod
    def categorize(cls, files: Iterable[Path], *, subtypes: bool = False) -> Mapping[FileType, Collection[Path]]:
        """Detects the filetypes for several files at once and categorizes them.

        Args:
            files: Files to deduce.
            subtypes: If True, the most specific matching subtype will be returned, othewise use the general subtype.

        Returns:
            A mapping files by ``FileType``. Unrecognized files are placed under ``FileType.ALL``.
        """
        categorized: defaultdict[FileType, list[Path]] = defaultdict(list)

        for file in files:
            ft = cls.detect(file, subtypes=subtypes) or FileType.ALL
            categorized[ft].append(file)

        return categorized

    def __str__(self) -> str:
        """Colon alias for this file type, for example ``:cxx.header``."""
        return self.value.name

    @property
    def name(self) -> str:
        """Colon alias for this file type, for example ``:cxx.header``."""
        return self.value.name

    @property
    def extensions(self) -> Iterable[str]:
        """Extensions for this file type starting with a dot, for example ``[".py"]``."""
        return self.value.extensions

    @property
    def globs(self) -> Iterable[str]:
        """Extensions with a star in the front, for example ``["*.c", "*.h"]``"""
        return (f"*{ext}" for ext in self.value.extensions)

    @property
    def subtypes(self) -> Iterable[str]:
        """More specialized sub-type names of this file type, if applicable.

        For example, general ``:cxx`` can be specified in a more granular way with ``:cxx.source`` or ``:cxx.header``.
        """
        return (ft.name for ft in self.value.subtypes)

    def matches(self, file: Path | str) -> bool:
        """Check if a given file name matches this FileType.

        Args:
            file: Name of file to check.

        Returns:
            True if the file's extension matches this FileType.
        """
        file = str(file)
        return any(file.endswith(ext) for ext in self.extensions)

    def to_json(self, indent: int | None = None) -> str:
        """Return JSON representation of this file type.

        Args:
            indent: Spaces to indent by, None for compact JSON.
        """
        return self.value.model_dump_json(indent=indent, exclude_defaults=True)
