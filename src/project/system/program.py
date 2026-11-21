import shutil
import time
from functools import cache
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING, Any, ClassVar, Self

from pydantic import BaseModel

from project.core.error import user
from project.core.logger import Log
from project.core.units import Duration, s
from project.format.sarif import SarifTool, SarifToolComponent

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = Log.get(__name__)


class Program(BaseModel):
    name: str
    path: Path
    version: str
    uri: ClassVar[str | None] = None

    def execute(
        self,
        args: Iterable[Any] | None,
        *,
        check: bool = True,
        capture: bool = True,
        timeout: Duration | None = None,
    ) -> CompletedProcess[str]:
        return execute(self.path, args, check=check, capture=capture, timeout=timeout)

    def sarif(self) -> SarifTool:
        """Sarif tool section for this program."""
        return SarifTool(
            driver=SarifToolComponent(
                name=self.name,
                information_uri=self.uri,
                version=self.version,
            )
        )

    @classmethod
    def tool(cls, name: str | None = None, version_command: tuple[str, ...] = ("--version",)) -> Self:
        name = name or cls.__name__.lower()
        return cls.model_validate(find_program(name, version_command=version_command).model_dump())


@cache
def find_program(name: str | Path, *, version_command: tuple[str, ...] = ("--version",)) -> Program:
    path = shutil.which(name)
    if not path:
        raise user.MissingProgramError(program=name)
    path = Path(path)

    if not isinstance(name, str):
        name = path.stem

    version = run([path, *version_command], capture_output=True, text=True, check=False, timeout=0.5).stdout or ""  # noqa: S603
    # Maybe we should symlink this path in .cache?
    return Program(name=name, path=path.absolute(), version=version)


def execute(
    executable: Path | str,
    args: Iterable[Any] | None = None,
    *,
    check: bool = True,
    capture: bool = True,
    timeout: Duration | None = None,
) -> CompletedProcess[str]:
    """Run a short-lived program and immediately collect its output text.

    Args:
        executable: Path to an existing program, or the name of a program to look up.
        args: Arguments to pass to the program, stringified.
        check: Set to false to manually inspect the return code instead of throwing.
        capture: Set to ``False`` to forward stdout/stderr to the controlling shell.
        timeout: Max time to wait for the process to finish; ``None`` for no limit.

    Returns:
        Standard subprocess.CompletedProcess[str].
    """
    program = find_program(executable)
    args = [str(a) for a in args or []]
    with logger.span("program.run", {"path": str(program.path), "version": program.version}, level=Log.NOTICE) as span:
        cmd: list[str] = [str(program.path), *args]
        timeout_s = timeout.to(s).m if timeout else None

        start_s = time.perf_counter()
        process = run(cmd, capture_output=capture, text=True, check=check, timeout=timeout_s)  # noqa: S603
        duration_s = time.perf_counter() - start_s

        span.log(
            span.level,
            " ".join(args),
            code=process.returncode,
            seconds=duration_s,
            bytes_streamed=len(process.stdout or "") + len(process.stderr or ""),
        )
    return process
