from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar, Literal
lazy from pathlib import Path

from pydantic import Field

from project.core.dirs import build_dir, build_stage_dir, project_dir
from project.formats.sarif import Sarif
from project.tools.tool import Tool

if TYPE_CHECKING:
    from collections.abc import Mapping

type Value = str | list[str] | bool


class Var(StrEnum):
    BUILD_RPATH_USE_ORIGIN = "CMAKE_BUILD_RPATH_USE_ORIGIN"
    BUILD_SHARED_LIBS = "BUILD_SHARED_LIBS"
    BUILD_TESTING = "BUILD_TESTING"
    BUILD_WITH_INSTALL_RPATH = "CMAKE_BUILD_WITH_INSTALL_RPATH"
    COLOR_DIAGNOSTICS = "CMAKE_COLOR_DIAGNOSTICS"
    CXX_SCAN_FOR_MODULES = "CMAKE_CXX_SCAN_FOR_MODULES"
    EXPORT_COMPILE_COMMANDS = "CMAKE_EXPORT_COMPILE_COMMANDS"
    INSTALL_PREFIX = "CMAKE_INSTALL_PREFIX"  # --prefix
    INSTALL_RPATH = "CMAKE_INSTALL_RPATH"
    LINKER_TYPE = "CMAKE_LINKER_TYPE"
    MESSAGE_CONTEXT_SHOW = "CMAKE_MESSAGE_CONTEXT_SHOW"  # --log-context
    PROGRAM_PATH = "CMAKE_PROGRAM_PATH"
    SKIP_TEST_ALL_DEPENDENCY = "CMAKE_SKIP_TEST_ALL_DEPENDENCY"  # false


class CMake(Tool):
    uri: ClassVar[str] = "https://cmake.org/cmake/help/latest/"

    source_dir: Path = project_dir()
    generator: Literal["Ninja", "FASTBuild", "Unix Makefiles"] = "Ninja"
    preset: str = ""
    variables: dict[Var, Value] = Field(
        default_factory=lambda: {
            Var.COLOR_DIAGNOSTICS: True,
            # Var.CXX_FLAGS: "-fdiagnostics-add-output=sarif:version=2.1",
        }
    )

    @property
    def build_dir(self) -> Path:
        return build_dir() / (self.preset or "default")

    async def configure(self, *, cache: Mapping[Var, Value] | None = None) -> Sarif:
        cache = cache or {}
        sarif_file = build_stage_dir() / "cmake.sarif"
        args = [
            "-S",
            self.source_dir,
            "-B",
            self.build_dir,
            "--sarif-output",
            sarif_file,
            *(f"-D{variable}={value}" for variable, value in {**self.variables, **cache}.items()),
        ]
        if self.preset:
            args.append(f"--preset={self.preset}")
        async with self.stream(
            args,
            env={
                "CFLAGS": "-fdiagnostics-add-output=sarif:version=2.1",
                "CXXFLAGS": "-fdiagnostics-add-output=sarif:version=2.1",
            },
        ) as proc:
            await proc.wait()
            return Sarif.from_file(sarif_file)

    async def build(self, *, target: str = "all") -> None:
        # args = ["--build", self.build_dir, "--target", target]
        args = ["--build"]
        if self.preset:
            args.append(f"--preset={self.preset}")
        async with self.stream(args) as proc:
            await proc.wait()

    async def install(self) -> None:
        pass

    def test(self) -> None:
        pass


# --sarif-output=file
